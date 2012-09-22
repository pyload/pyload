#!/usr/bin/env python
#
# Copyright 2012, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# A copy of standalone.py with uneeded stuff removed
# some logging methods removed
# Added api attribute to request

import BaseHTTPServer
import CGIHTTPServer
import SocketServer
import httplib
import logging
import os
import re
import select
import socket
import sys
import threading

_HAS_SSL = False
_HAS_OPEN_SSL = False

from mod_pywebsocket import common
from mod_pywebsocket import dispatch
from mod_pywebsocket import handshake
from mod_pywebsocket import http_header_util
from mod_pywebsocket import memorizingfile
from mod_pywebsocket import util


_DEFAULT_REQUEST_QUEUE_SIZE = 128

# 1024 is practically large enough to contain WebSocket handshake lines.
_MAX_MEMORIZED_LINES = 1024

def import_ssl():
    global _HAS_SSL, _HAS_OPEN_SSL
    try:
        import ssl
        _HAS_SSL = True
    except ImportError:
        try:
            import OpenSSL.SSL
            _HAS_OPEN_SSL = True
        except ImportError:
            pass


class _StandaloneConnection(object):
    """Mimic mod_python mp_conn."""

    def __init__(self, request_handler):
        """Construct an instance.

        Args:
            request_handler: A WebSocketRequestHandler instance.
        """

        self._request_handler = request_handler

    def get_local_addr(self):
        """Getter to mimic mp_conn.local_addr."""

        return (self._request_handler.server.server_name,
                self._request_handler.server.server_port)
    local_addr = property(get_local_addr)

    def get_remote_addr(self):
        """Getter to mimic mp_conn.remote_addr.

        Setting the property in __init__ won't work because the request
        handler is not initialized yet there."""

        return self._request_handler.client_address
    remote_addr = property(get_remote_addr)

    def write(self, data):
        """Mimic mp_conn.write()."""

        return self._request_handler.wfile.write(data)

    def read(self, length):
        """Mimic mp_conn.read()."""

        return self._request_handler.rfile.read(length)

    def get_memorized_lines(self):
        """Get memorized lines."""

        return self._request_handler.rfile.get_memorized_lines()


class _StandaloneRequest(object):
    """Mimic mod_python request."""

    def __init__(self, request_handler, use_tls):
        """Construct an instance.

        Args:
            request_handler: A WebSocketRequestHandler instance.
        """

        self._logger = logging.getLogger("log")
        self.api = None

        self._request_handler = request_handler
        self.connection = _StandaloneConnection(request_handler)
        self._use_tls = use_tls
        self.headers_in = request_handler.headers

    def get_uri(self):
        """Getter to mimic request.uri."""

        return self._request_handler.path
    uri = property(get_uri)

    def get_method(self):
        """Getter to mimic request.method."""

        return self._request_handler.command
    method = property(get_method)

    def is_https(self):
        """Mimic request.is_https()."""

        return self._use_tls

    def _drain_received_data(self):
        """Don't use this method from WebSocket handler. Drains unread data
        in the receive buffer.
        """

        raw_socket = self._request_handler.connection
        drained_data = util.drain_received_data(raw_socket)

        if drained_data:
            self._logger.debug(
                'Drained data following close frame: %r', drained_data)


class _StandaloneSSLConnection(object):
    """A wrapper class for OpenSSL.SSL.Connection to provide makefile method
    which is not supported by the class.
    """

    def __init__(self, connection):
        self._connection = connection

    def __getattribute__(self, name):
        if name in ('_connection', 'makefile'):
            return object.__getattribute__(self, name)
        return self._connection.__getattribute__(name)

    def __setattr__(self, name, value):
        if name in ('_connection', 'makefile'):
            return object.__setattr__(self, name, value)
        return self._connection.__setattr__(name, value)

    def makefile(self, mode='r', bufsize=-1):
        return socket._fileobject(self._connection, mode, bufsize)


class WebSocketServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """HTTPServer specialized for WebSocket."""

    # Overrides SocketServer.ThreadingMixIn.daemon_threads
    daemon_threads = True
    # Overrides BaseHTTPServer.HTTPServer.allow_reuse_address
    allow_reuse_address = True

    def __init__(self, options):
        """Override SocketServer.TCPServer.__init__ to set SSL enabled
        socket object to self.socket before server_bind and server_activate,
        if necessary.
        """

        self._logger = logging.getLogger("log")

        self.request_queue_size = options.request_queue_size
        self.__ws_is_shut_down = threading.Event()
        self.__ws_serving = False

        SocketServer.BaseServer.__init__(
            self, (options.server_host, options.port), WebSocketRequestHandler)

        # Expose the options object to allow handler objects access it. We name
        # it with websocket_ prefix to avoid conflict.
        self.websocket_server_options = options

        self._create_sockets()
        self.server_bind()
        self.server_activate()

    def _create_sockets(self):
        self.server_name, self.server_port = self.server_address
        self._sockets = []
        if not self.server_name:
            # On platforms that doesn't support IPv6, the first bind fails.
            # On platforms that supports IPv6
            # - If it binds both IPv4 and IPv6 on call with AF_INET6, the
            #   first bind succeeds and the second fails (we'll see 'Address
            #   already in use' error).
            # - If it binds only IPv6 on call with AF_INET6, both call are
            #   expected to succeed to listen both protocol.
            addrinfo_array = [
                (socket.AF_INET6, socket.SOCK_STREAM, '', '', ''),
                (socket.AF_INET, socket.SOCK_STREAM, '', '', '')]
        else:
            addrinfo_array = socket.getaddrinfo(self.server_name,
                self.server_port,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP)
        for addrinfo in addrinfo_array:
            family, socktype, proto, canonname, sockaddr = addrinfo
            try:
                socket_ = socket.socket(family, socktype)
            except Exception, e:
                self._logger.info('Skip by failure: %r', e)
                continue
            if self.websocket_server_options.use_tls:
                if _HAS_SSL:
                    if self.websocket_server_options.ca_certificate:
                        client_cert_ = ssl.CERT_REQUIRED
                    else:
                        client_cert_ = ssl.CERT_NONE
                    socket_ = ssl.wrap_socket(socket_,
                        keyfile=self.websocket_server_options.private_key,
                        certfile=self.websocket_server_options.certificate,
                        ssl_version=ssl.PROTOCOL_SSLv23,
                        ca_certs=self.websocket_server_options.ca_certificate,
                        cert_reqs=client_cert_)
                if _HAS_OPEN_SSL:
                    ctx = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)
                    ctx.use_privatekey_file(
                        self.websocket_server_options.private_key)
                    ctx.use_certificate_file(
                        self.websocket_server_options.certificate)
                    socket_ = OpenSSL.SSL.Connection(ctx, socket_)
            self._sockets.append((socket_, addrinfo))

    def server_bind(self):
        """Override SocketServer.TCPServer.server_bind to enable multiple
        sockets bind.
        """

        failed_sockets = []

        for socketinfo in self._sockets:
            socket_, addrinfo = socketinfo
            if self.allow_reuse_address:
                socket_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                socket_.bind(self.server_address)
            except Exception, e:
                self._logger.info('Skip by failure: %r', e)
                socket_.close()
                failed_sockets.append(socketinfo)

        for socketinfo in failed_sockets:
            self._sockets.remove(socketinfo)

    def server_activate(self):
        """Override SocketServer.TCPServer.server_activate to enable multiple
        sockets listen.
        """

        failed_sockets = []

        for socketinfo in self._sockets:
            socket_, addrinfo = socketinfo
            self._logger.debug('Listen on: %r', addrinfo)
            try:
                socket_.listen(self.request_queue_size)
            except Exception, e:
                self._logger.info('Skip by failure: %r', e)
                socket_.close()
                failed_sockets.append(socketinfo)

        for socketinfo in failed_sockets:
            self._sockets.remove(socketinfo)

    def server_close(self):
        """Override SocketServer.TCPServer.server_close to enable multiple
        sockets close.
        """

        for socketinfo in self._sockets:
            socket_, addrinfo = socketinfo
            self._logger.info('Close on: %r', addrinfo)
            socket_.close()

    def fileno(self):
        """Override SocketServer.TCPServer.fileno."""

        self._logger.critical('Not supported: fileno')
        return self._sockets[0][0].fileno()

    def handle_error(self, rquest, client_address):
        """Override SocketServer.handle_error."""

        self._logger.error(
            'Exception in processing request from: %r\n%s',
            client_address,
            util.get_stack_trace())
        # Note: client_address is a tuple.

    def get_request(self):
        """Override TCPServer.get_request to wrap OpenSSL.SSL.Connection
        object with _StandaloneSSLConnection to provide makefile method. We
        cannot substitute OpenSSL.SSL.Connection.makefile since it's readonly
        attribute.
        """

        accepted_socket, client_address = self.socket.accept()
        if self.websocket_server_options.use_tls and _HAS_OPEN_SSL:
            accepted_socket = _StandaloneSSLConnection(accepted_socket)
        return accepted_socket, client_address

    def serve_forever(self, poll_interval=0.5):
        """Override SocketServer.BaseServer.serve_forever."""

        self.__ws_serving = True
        self.__ws_is_shut_down.clear()
        handle_request = self.handle_request
        if hasattr(self, '_handle_request_noblock'):
            handle_request = self._handle_request_noblock
        else:
            self._logger.warning('Fallback to blocking request handler')
        try:
            while self.__ws_serving:
                r, w, e = select.select(
                    [socket_[0] for socket_ in self._sockets],
                    [], [], poll_interval)
                for socket_ in r:
                    self.socket = socket_
                    handle_request()
                self.socket = None
        finally:
            self.__ws_is_shut_down.set()

    def shutdown(self):
        """Override SocketServer.BaseServer.shutdown."""

        self.__ws_serving = False
        self.__ws_is_shut_down.wait()


class WebSocketRequestHandler(CGIHTTPServer.CGIHTTPRequestHandler):
    """CGIHTTPRequestHandler specialized for WebSocket."""

    # Use httplib.HTTPMessage instead of mimetools.Message.
    MessageClass = httplib.HTTPMessage

    def setup(self):
        """Override SocketServer.StreamRequestHandler.setup to wrap rfile
        with MemorizingFile.

        This method will be called by BaseRequestHandler's constructor
        before calling BaseHTTPRequestHandler.handle.
        BaseHTTPRequestHandler.handle will call
        BaseHTTPRequestHandler.handle_one_request and it will call
        WebSocketRequestHandler.parse_request.
        """

        # Call superclass's setup to prepare rfile, wfile, etc. See setup
        # definition on the root class SocketServer.StreamRequestHandler to
        # understand what this does.
        CGIHTTPServer.CGIHTTPRequestHandler.setup(self)

        self.rfile = memorizingfile.MemorizingFile(
            self.rfile,
            max_memorized_lines=_MAX_MEMORIZED_LINES)

    def __init__(self, request, client_address, server):
        self._logger = util.get_class_logger(self)

        self._options = server.websocket_server_options

        # Overrides CGIHTTPServerRequestHandler.cgi_directories.
        self.cgi_directories = self._options.cgi_directories
        # Replace CGIHTTPRequestHandler.is_executable method.
        if self._options.is_executable_method is not None:
            self.is_executable = self._options.is_executable_method

        # This actually calls BaseRequestHandler.__init__.
        CGIHTTPServer.CGIHTTPRequestHandler.__init__(
            self, request, client_address, server)

    def parse_request(self):
        """Override BaseHTTPServer.BaseHTTPRequestHandler.parse_request.

        Return True to continue processing for HTTP(S), False otherwise.

        See BaseHTTPRequestHandler.handle_one_request method which calls
        this method to understand how the return value will be handled.
        """

        # We hook parse_request method, but also call the original
        # CGIHTTPRequestHandler.parse_request since when we return False,
        # CGIHTTPRequestHandler.handle_one_request continues processing and
        # it needs variables set by CGIHTTPRequestHandler.parse_request.
        #
        # Variables set by this method will be also used by WebSocket request
        # handling (self.path, self.command, self.requestline, etc. See also
        # how _StandaloneRequest's members are implemented using these
        # attributes).
        if not CGIHTTPServer.CGIHTTPRequestHandler.parse_request(self):
            return False
        host, port, resource = http_header_util.parse_uri(self.path)
        if resource is None:
            self._logger.info('Invalid URI: %r', self.path)
            self._logger.info('Fallback to CGIHTTPRequestHandler')
            return True
        server_options = self.server.websocket_server_options
        if host is not None:
            validation_host = server_options.validation_host
            if validation_host is not None and host != validation_host:
                self._logger.info('Invalid host: %r (expected: %r)',
                    host,
                    validation_host)
                self._logger.info('Fallback to CGIHTTPRequestHandler')
                return True
        if port is not None:
            validation_port = server_options.validation_port
            if validation_port is not None and port != validation_port:
                self._logger.info('Invalid port: %r (expected: %r)',
                    port,
                    validation_port)
                self._logger.info('Fallback to CGIHTTPRequestHandler')
                return True
        self.path = resource

        request = _StandaloneRequest(self, self._options.use_tls)

        try:
            # Fallback to default http handler for request paths for which
            # we don't have request handlers.
            if not self._options.dispatcher.get_handler_suite(self.path):
                self._logger.info('No handler for resource: %r',
                    self.path)
                self._logger.info('Fallback to CGIHTTPRequestHandler')
                return True
        except dispatch.DispatchException, e:
            self._logger.info('%s', e)
            self.send_error(e.status)
            return False

        # If any Exceptions without except clause setup (including
        # DispatchException) is raised below this point, it will be caught
        # and logged by WebSocketServer.

        try:
            try:
                handshake.do_handshake(
                    request,
                    self._options.dispatcher,
                    allowDraft75=self._options.allow_draft75,
                    strict=self._options.strict)
            except handshake.VersionException, e:
                self._logger.info('%s', e)
                self.send_response(common.HTTP_STATUS_BAD_REQUEST)
                self.send_header(common.SEC_WEBSOCKET_VERSION_HEADER,
                    e.supported_versions)
                self.end_headers()
                return False
            except handshake.HandshakeException, e:
                # Handshake for ws(s) failed.
                self._logger.info('%s', e)
                self.send_error(e.status)
                return False

            request._dispatcher = self._options.dispatcher
            self._options.dispatcher.transfer_data(request)
        except handshake.AbortedByUserException, e:
            self._logger.info('%s', e)
        return False

    def log_request(self, code='-', size='-'):
        """Override BaseHTTPServer.log_request."""

        self._logger.info('"%s" %s %s',
            self.requestline, str(code), str(size))

    def log_error(self, *args):
        """Override BaseHTTPServer.log_error."""

        # Despite the name, this method is for warnings than for errors.
        # For example, HTTP status code is logged by this method.
        self._logger.warning('%s - %s',
            self.address_string(),
            args[0] % args[1:])

    def is_cgi(self):
        """Test whether self.path corresponds to a CGI script.

        Add extra check that self.path doesn't contains ..
        Also check if the file is a executable file or not.
        If the file is not executable, it is handled as static file or dir
        rather than a CGI script.
        """

        if CGIHTTPServer.CGIHTTPRequestHandler.is_cgi(self):
            if '..' in self.path:
                return False
                # strip query parameter from request path
            resource_name = self.path.split('?', 2)[0]
            # convert resource_name into real path name in filesystem.
            scriptfile = self.translate_path(resource_name)
            if not os.path.isfile(scriptfile):
                return False
            if not self.is_executable(scriptfile):
                return False
            return True
        return False


def _get_logger_from_class(c):
    return logging.getLogger('%s.%s' % (c.__module__, c.__name__))


def _alias_handlers(dispatcher, websock_handlers_map_file):
    """Set aliases specified in websock_handler_map_file in dispatcher.

    Args:
        dispatcher: dispatch.Dispatcher instance
        websock_handler_map_file: alias map file
    """

    fp = open(websock_handlers_map_file)
    try:
        for line in fp:
            if line[0] == '#' or line.isspace():
                continue
            m = re.match('(\S+)\s+(\S+)', line)
            if not m:
                logging.warning('Wrong format in map file:' + line)
                continue
            try:
                dispatcher.add_resource_path_alias(
                    m.group(1), m.group(2))
            except dispatch.DispatchException, e:
                logging.error(str(e))
    finally:
        fp.close()

class DefaultOptions:
    server_host = ''
    port = common.DEFAULT_WEB_SOCKET_PORT
    use_tls = False
    private_key = ''
    certificate = ''
    ca_certificate = ''
    dispatcher = None
    request_queue_size = _DEFAULT_REQUEST_QUEUE_SIZE

    allow_draft75 = False
    strict = False
    validation_host = None
    validation_port = None
    cgi_directories = ''
    is_executable_method = False

def _main(args=None):
    options, args = _parse_args_and_config(args=args)

    os.chdir(options.document_root)

    _configure_logging(options)

    # TODO(tyoshino): Clean up initialization of CGI related values. Move some
    # of code here to WebSocketRequestHandler class if it's better.
    options.cgi_directories = []
    options.is_executable_method = None
    if options.cgi_paths:
        options.cgi_directories = options.cgi_paths.split(',')
        if sys.platform in ('cygwin', 'win32'):
            cygwin_path = None
            # For Win32 Python, it is expected that CYGWIN_PATH
            # is set to a directory of cygwin binaries.
            # For example, websocket_server.py in Chromium sets CYGWIN_PATH to
            # full path of third_party/cygwin/bin.
            if 'CYGWIN_PATH' in os.environ:
                cygwin_path = os.environ['CYGWIN_PATH']
            util.wrap_popen3_for_win(cygwin_path)

            def __check_script(scriptpath):
                return util.get_script_interp(scriptpath, cygwin_path)

            options.is_executable_method = __check_script

    if options.use_tls:
        if not (_HAS_SSL or _HAS_OPEN_SSL):
            logging.critical('TLS support requires ssl or pyOpenSSL module.')
            sys.exit(1)
        if not options.private_key or not options.certificate:
            logging.critical(
                'To use TLS, specify private_key and certificate.')
            sys.exit(1)

    if options.ca_certificate:
        if not options.use_tls:
            logging.critical('TLS must be enabled for client authentication.')
            sys.exit(1)
        if not _HAS_SSL:
            logging.critical('Client authentication requires ssl module.')

    if not options.scan_dir:
        options.scan_dir = options.websock_handlers

    try:
        if options.thread_monitor_interval_in_sec > 0:
            # Run a thread monitor to show the status of server threads for
            # debugging.
            ThreadMonitor(options.thread_monitor_interval_in_sec).start()

        # Share a Dispatcher among request handlers to save time for
        # instantiation.  Dispatcher can be shared because it is thread-safe.
        options.dispatcher = dispatch.Dispatcher(
            options.websock_handlers,
            options.scan_dir,
            options.allow_handlers_outside_root_dir)
        if options.websock_handlers_map_file:
            _alias_handlers(options.dispatcher,
                options.websock_handlers_map_file)
        warnings = options.dispatcher.source_warnings()
        if warnings:
            for warning in warnings:
                logging.warning('mod_pywebsocket: %s' % warning)

        server = WebSocketServer(options)
        server.serve_forever()
    except Exception, e:
        logging.critical('mod_pywebsocket: %s' % e)
        logging.critical('mod_pywebsocket: %s' % util.get_stack_trace())
        sys.exit(1)


if __name__ == '__main__':
    _main(sys.argv[1:])


# vi:sts=4 sw=4 et
