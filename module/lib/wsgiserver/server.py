"""
A high-speed, production ready, thread pooled, generic HTTP server.

For those of you wanting to understand internals of this module, here's the
basic call flow. The server's listening thread runs a very tight loop,
sticking incoming connections onto a Queue::

    server = HTTPServer(...)
    server.start()
    while True:
        tick()
        # This blocks until a request comes in:
        child = socket.accept()
        conn = HTTPConnection(child, ...)
        server.requests.put(conn)

Worker threads are kept in a pool and poll the Queue, popping off and then
handling each connection in turn. Each connection can consist of an arbitrary
number of requests and their responses, so we run a nested loop::

    while True:
        conn = server.requests.get()
        conn.communicate()
        ->  while True:
                req = HTTPRequest(...)
                req.parse_request()
                ->  # Read the Request-Line, e.g. "GET /page HTTP/1.1"
                    req.rfile.readline()
                    read_headers(req.rfile, req.inheaders)
                req.respond()
                ->  response = app(...)
                    try:
                        for chunk in response:
                            if chunk:
                                req.write(chunk)
                    finally:
                        if hasattr(response, "close"):
                            response.close()
                if req.close_connection:
                    return

And now for a trivial doctest to exercise the test suite

>>> 'HTTPServer' in globals()
True

"""

import os
import io
import re
import email.utils
import socket
import sys
import time
import traceback as traceback_
import logging
import platform

import six
from six.moves import queue
from six.moves import urllib

from . import errors, __version__
from ._compat import bton, ntou
from .workers import threadpool
from .makefile import MakeFile


__all__ = ('HTTPRequest', 'HTTPConnection', 'HTTPServer',
           'SizeCheckWrapper', 'KnownLengthRFile', 'ChunkedRFile',
           'Gateway', 'get_ssl_adapter_class')


if 'win' in sys.platform and hasattr(socket, 'AF_INET6'):
    if not hasattr(socket, 'IPPROTO_IPV6'):
        socket.IPPROTO_IPV6 = 41
    if not hasattr(socket, 'IPV6_V6ONLY'):
        socket.IPV6_V6ONLY = 27


LF = b'\n'
CRLF = b'\r\n'
TAB = b'\t'
SPACE = b' '
COLON = b':'
SEMICOLON = b';'
EMPTY = b''
ASTERISK = b'*'
FORWARD_SLASH = b'/'
QUOTED_SLASH = b'%2F'
QUOTED_SLASH_REGEX = re.compile(b'(?i)' + QUOTED_SLASH)


comma_separated_headers = [
    b'Accept', b'Accept-Charset', b'Accept-Encoding',
    b'Accept-Language', b'Accept-Ranges', b'Allow', b'Cache-Control',
    b'Connection', b'Content-Encoding', b'Content-Language', b'Expect',
    b'If-Match', b'If-None-Match', b'Pragma', b'Proxy-Authenticate', b'TE',
    b'Trailer', b'Transfer-Encoding', b'Upgrade', b'Vary', b'Via', b'Warning',
    b'WWW-Authenticate',
]


if not hasattr(logging, 'statistics'):
    logging.statistics = {}


class HeaderReader(object):
    """Object for reading headers from an HTTP request.

    Interface and default implementation.
    """

    def __call__(self, rfile, hdict=None):
        """
        Read headers from the given stream into the given header dict.

        If hdict is None, a new header dict is created. Returns the populated
        header dict.

        Headers which are repeated are folded together using a comma if their
        specification so dictates.

        This function raises ValueError when the read bytes violate the HTTP
        spec.
        You should probably return "400 Bad Request" if this happens.
        """
        if hdict is None:
            hdict = {}

        while True:
            line = rfile.readline()
            if not line:
                # No more data--illegal end of headers
                raise ValueError('Illegal end of headers.')

            if line == CRLF:
                # Normal end of headers
                break
            if not line.endswith(CRLF):
                raise ValueError('HTTP requires CRLF terminators')

            if line[0] in (SPACE, TAB):
                # It's a continuation line.
                v = line.strip()
            else:
                try:
                    k, v = line.split(COLON, 1)
                except ValueError:
                    raise ValueError('Illegal header line.')
                v = v.strip()
                k = self._transform_key(k)
                hname = k

            if not self._allow_header(k):
                continue

            if k in comma_separated_headers:
                existing = hdict.get(hname)
                if existing:
                    v = b', '.join((existing, v))
            hdict[hname] = v

        return hdict

    def _allow_header(self, key_name):
        return True

    def _transform_key(self, key_name):
        # TODO: what about TE and WWW-Authenticate?
        return key_name.strip().title()


class DropUnderscoreHeaderReader(HeaderReader):
    """Custom HeaderReader to exclude any headers with underscores in them."""

    def _allow_header(self, key_name):
        orig = super(DropUnderscoreHeaderReader, self)._allow_header(key_name)
        return orig and '_' not in key_name


class SizeCheckWrapper(object):
    """Wraps a file-like object, raising MaxSizeExceeded if too large."""

    def __init__(self, rfile, maxlen):
        """Initialize SizeCheckWrapper instance.

        Args:
            rfile (file): file of a limited size
            maxlen (int): maximum length of the file being read
        """
        self.rfile = rfile
        self.maxlen = maxlen
        self.bytes_read = 0

    def _check_length(self):
        if self.maxlen and self.bytes_read > self.maxlen:
            raise errors.MaxSizeExceeded()

    def read(self, size=None):
        """Read a chunk from rfile buffer and return it.

        Args:
            size (int): amount of data to read

        Returns:
            bytes: Chunk from rfile, limited by size if specified.
        """
        data = self.rfile.read(size)
        self.bytes_read += len(data)
        self._check_length()
        return data

    def readline(self, size=None):
        """Read a single line from rfile buffer and return it.

        Args:
            size (int): minimum amount of data to read

        Returns:
            bytes: One line from rfile.
        """
        if size is not None:
            data = self.rfile.readline(size)
            self.bytes_read += len(data)
            self._check_length()
            return data

        # User didn't specify a size ...
        # We read the line in chunks to make sure it's not a 100MB line !
        res = []
        while True:
            data = self.rfile.readline(256)
            self.bytes_read += len(data)
            self._check_length()
            res.append(data)
            # See https://github.com/cherrypy/cherrypy/issues/421
            if len(data) < 256 or data[-1:] == LF:
                return EMPTY.join(res)

    def readlines(self, sizehint=0):
        """Read all lines from rfile buffer and return them.

        Args:
            sizehint (int): hint of minimum amount of data to read

        Returns:
            list[bytes]: Lines of bytes read from rfile.
        """
        # Shamelessly stolen from StringIO
        total = 0
        lines = []
        line = self.readline(sizehint)
        while line:
            lines.append(line)
            total += len(line)
            if 0 < sizehint <= total:
                break
            line = self.readline(sizehint)
        return lines

    def close(self):
        """Release resources allocated for rfile."""
        self.rfile.close()

    def __iter__(self):
        """Return file iterator."""
        return self

    def __next__(self):
        """Generate next file chunk."""
        data = next(self.rfile)
        self.bytes_read += len(data)
        self._check_length()
        return data

    def next(self):
        """Generate next file chunk."""
        data = self.rfile.next()
        self.bytes_read += len(data)
        self._check_length()
        return data


class KnownLengthRFile(object):
    """Wraps a file-like object, returning an empty string when exhausted."""

    def __init__(self, rfile, content_length):
        """Initialize KnownLengthRFile instance.

        Args:
            rfile (file): file of a known size
            content_length (int): length of the file being read
        """
        self.rfile = rfile
        self.remaining = content_length

    def read(self, size=None):
        """Read a chunk from rfile buffer and return it.

        Args:
            size (int): amount of data to read

        Returns:
            bytes: Chunk from rfile, limited by size if specified.
        """
        if self.remaining == 0:
            return b''
        if size is None:
            size = self.remaining
        else:
            size = min(size, self.remaining)

        data = self.rfile.read(size)
        self.remaining -= len(data)
        return data

    def readline(self, size=None):
        """Read a single line from rfile buffer and return it.

        Args:
            size (int): minimum amount of data to read

        Returns:
            bytes: One line from rfile.
        """
        if self.remaining == 0:
            return b''
        if size is None:
            size = self.remaining
        else:
            size = min(size, self.remaining)

        data = self.rfile.readline(size)
        self.remaining -= len(data)
        return data

    def readlines(self, sizehint=0):
        """Read all lines from rfile buffer and return them.

        Args:
            sizehint (int): hint of minimum amount of data to read

        Returns:
            list[bytes]: Lines of bytes read from rfile.
        """
        # Shamelessly stolen from StringIO
        total = 0
        lines = []
        line = self.readline(sizehint)
        while line:
            lines.append(line)
            total += len(line)
            if 0 < sizehint <= total:
                break
            line = self.readline(sizehint)
        return lines

    def close(self):
        """Release resources allocated for rfile."""
        self.rfile.close()

    def __iter__(self):
        """Return file iterator."""
        return self

    def __next__(self):
        """Generate next file chunk."""
        data = next(self.rfile)
        self.remaining -= len(data)
        return data


class ChunkedRFile(object):
    """Wraps a file-like object, returning an empty string when exhausted.

    This class is intended to provide a conforming wsgi.input value for
    request entities that have been encoded with the 'chunked' transfer
    encoding.
    """

    def __init__(self, rfile, maxlen, bufsize=8192):
        """Initialize ChunkedRFile instance.

        Args:
            rfile (file): file encoded with the 'chunked' transfer encoding
            maxlen (int): maximum length of the file being read
            bufsize (int): size of the buffer used to read the file
        """
        self.rfile = rfile
        self.maxlen = maxlen
        self.bytes_read = 0
        self.buffer = EMPTY
        self.bufsize = bufsize
        self.closed = False

    def _fetch(self):
        if self.closed:
            return

        line = self.rfile.readline()
        self.bytes_read += len(line)

        if self.maxlen and self.bytes_read > self.maxlen:
            raise errors.MaxSizeExceeded(
                'Request Entity Too Large', self.maxlen)

        line = line.strip().split(SEMICOLON, 1)

        try:
            chunk_size = line.pop(0)
            chunk_size = int(chunk_size, 16)
        except ValueError:
            raise ValueError('Bad chunked transfer size: ' + repr(chunk_size))

        if chunk_size <= 0:
            self.closed = True
            return

#            if line: chunk_extension = line[0]

        if self.maxlen and self.bytes_read + chunk_size > self.maxlen:
            raise IOError('Request Entity Too Large')

        chunk = self.rfile.read(chunk_size)
        self.bytes_read += len(chunk)
        self.buffer += chunk

        crlf = self.rfile.read(2)
        if crlf != CRLF:
            raise ValueError(
                "Bad chunked transfer coding (expected '\\r\\n', "
                'got ' + repr(crlf) + ')')

    def read(self, size=None):
        """Read a chunk from rfile buffer and return it.

        Args:
            size (int): amount of data to read

        Returns:
            bytes: Chunk from rfile, limited by size if specified.
        """
        data = EMPTY

        if size == 0:
            return data

        while True:
            if size and len(data) >= size:
                return data

            if not self.buffer:
                self._fetch()
                if not self.buffer:
                    # EOF
                    return data

            if size:
                remaining = size - len(data)
                data += self.buffer[:remaining]
                self.buffer = self.buffer[remaining:]
            else:
                data += self.buffer
                self.buffer = EMPTY

    def readline(self, size=None):
        """Read a single line from rfile buffer and return it.

        Args:
            size (int): minimum amount of data to read

        Returns:
            bytes: One line from rfile.
        """
        data = EMPTY

        if size == 0:
            return data

        while True:
            if size and len(data) >= size:
                return data

            if not self.buffer:
                self._fetch()
                if not self.buffer:
                    # EOF
                    return data

            newline_pos = self.buffer.find(LF)
            if size:
                if newline_pos == -1:
                    remaining = size - len(data)
                    data += self.buffer[:remaining]
                    self.buffer = self.buffer[remaining:]
                else:
                    remaining = min(size - len(data), newline_pos)
                    data += self.buffer[:remaining]
                    self.buffer = self.buffer[remaining:]
            else:
                if newline_pos == -1:
                    data += self.buffer
                    self.buffer = EMPTY
                else:
                    data += self.buffer[:newline_pos]
                    self.buffer = self.buffer[newline_pos:]

    def readlines(self, sizehint=0):
        """Read all lines from rfile buffer and return them.

        Args:
            sizehint (int): hint of minimum amount of data to read

        Returns:
            list[bytes]: Lines of bytes read from rfile.
        """
        # Shamelessly stolen from StringIO
        total = 0
        lines = []
        line = self.readline(sizehint)
        while line:
            lines.append(line)
            total += len(line)
            if 0 < sizehint <= total:
                break
            line = self.readline(sizehint)
        return lines

    def read_trailer_lines(self):
        """Read HTTP headers and yield them.

        Returns:
            Generator: yields CRLF separated lines.
        """
        if not self.closed:
            raise ValueError(
                'Cannot read trailers until the request body has been read.')

        while True:
            line = self.rfile.readline()
            if not line:
                # No more data--illegal end of headers
                raise ValueError('Illegal end of headers.')

            self.bytes_read += len(line)
            if self.maxlen and self.bytes_read > self.maxlen:
                raise IOError('Request Entity Too Large')

            if line == CRLF:
                # Normal end of headers
                break
            if not line.endswith(CRLF):
                raise ValueError('HTTP requires CRLF terminators')

            yield line

    def close(self):
        """Release resources allocated for rfile."""
        self.rfile.close()


class HTTPRequest(object):
    """An HTTP Request (and response).

    A single HTTP connection may consist of multiple request/response pairs.
    """

    server = None
    """The HTTPServer object which is receiving this request."""

    conn = None
    """The HTTPConnection object on which this request connected."""

    inheaders = {}
    """A dict of request headers."""

    outheaders = []
    """A list of header tuples to write in the response."""

    ready = False
    """When True, the request has been parsed and is ready to begin generating
    the response. When False, signals the calling Connection that the response
    should not be generated and the connection should close."""

    close_connection = False
    """Signals the calling Connection that the request should close. This does
    not imply an error! The client and/or server may each request that the
    connection be closed."""

    chunked_write = False
    """If True, output will be encoded with the "chunked" transfer-coding.

    This value is set automatically inside send_headers."""

    header_reader = HeaderReader()
    """
    A HeaderReader instance or compatible reader.
    """

    def __init__(self, server, conn, proxy_mode=False, strict_mode=True):
        """Initialize HTTP request container instance.

        Args:
            server (HTTPServer): web server object receiving this request
            conn (HTTPConnection): HTTP connection object for this request
            proxy_mode (bool): whether this HTTPServer should behave as a PROXY
            server for certain requests
            strict_mode (bool): whether we should return a 400 Bad Request when
            we encounter a request that a HTTP compliant client should not be
            making
        """
        self.server = server
        self.conn = conn

        self.ready = False
        self.started_request = False
        self.scheme = b'http'
        if self.server.ssl_adapter is not None:
            self.scheme = b'https'
        # Use the lowest-common protocol in case read_request_line errors.
        self.response_protocol = 'HTTP/1.0'
        self.inheaders = {}

        self.status = ''
        self.outheaders = []
        self.sent_headers = False
        self.close_connection = self.__class__.close_connection
        self.chunked_read = False
        self.chunked_write = self.__class__.chunked_write
        self.proxy_mode = proxy_mode
        self.strict_mode = strict_mode

    def parse_request(self):
        """Parse the next HTTP request start-line and message-headers."""
        self.rfile = SizeCheckWrapper(self.conn.rfile,
                                      self.server.max_request_header_size)
        try:
            success = self.read_request_line()
        except errors.MaxSizeExceeded:
            self.simple_response(
                '414 Request-URI Too Long',
                'The Request-URI sent with the request exceeds the maximum '
                'allowed bytes.')
            return
        else:
            if not success:
                return

        try:
            success = self.read_request_headers()
        except errors.MaxSizeExceeded:
            self.simple_response(
                '413 Request Entity Too Large',
                'The headers sent with the request exceed the maximum '
                'allowed bytes.')
            return
        else:
            if not success:
                return

        self.ready = True

    def read_request_line(self):
        """Read and parse first line of the HTTP request.

        Returns:
            bool: True if the request line is valid or False if it's malformed.
        """
        # HTTP/1.1 connections are persistent by default. If a client
        # requests a page, then idles (leaves the connection open),
        # then rfile.readline() will raise socket.error("timed out").
        # Note that it does this based on the value given to settimeout(),
        # and doesn't need the client to request or acknowledge the close
        # (although your TCP stack might suffer for it: cf Apache's history
        # with FIN_WAIT_2).
        request_line = self.rfile.readline()

        # Set started_request to True so communicate() knows to send 408
        # from here on out.
        self.started_request = True
        if not request_line:
            return False

        if request_line == CRLF:
            # RFC 2616 sec 4.1: "...if the server is reading the protocol
            # stream at the beginning of a message and receives a CRLF
            # first, it should ignore the CRLF."
            # But only ignore one leading line! else we enable a DoS.
            request_line = self.rfile.readline()
            if not request_line:
                return False

        if not request_line.endswith(CRLF):
            self.simple_response(
                '400 Bad Request', 'HTTP requires CRLF terminators')
            return False

        try:
            method, uri, req_protocol = request_line.strip().split(SPACE, 2)
            if not req_protocol.startswith(b'HTTP/'):
                self.simple_response(
                    '400 Bad Request', 'Malformed Request-Line: bad protocol'
                )
                return False
            rp = req_protocol[5:].split(b'.', 1)
            rp = tuple(map(int, rp))  # Minor.Major must be threat as integers
            if rp > (1, 1):
                self.simple_response(
                    '505 HTTP Version Not Supported', 'Cannot fulfill request'
                )
                return False
        except (ValueError, IndexError):
            self.simple_response('400 Bad Request', 'Malformed Request-Line')
            return False

        self.uri = uri
        self.method = method.upper()

        if self.strict_mode and method != self.method:
            resp = (
                'Malformed method name: According to RFC 2616 '
                '(section 5.1.1) and its successors '
                'RFC 7230 (section 3.1.1) and RFC 7231 (section 4.1) '
                'method names are case-sensitive and uppercase.'
            )
            self.simple_response('400 Bad Request', resp)
            return False

        try:
            if six.PY2:  # FIXME: Figure out better way to do this
                # Ref: https://stackoverflow.com/a/196392/595220 (like this?)
                """This is a dummy check for unicode in URI."""
                ntou(bton(uri, 'ascii'), 'ascii')
            scheme, authority, path, qs, fragment = urllib.parse.urlsplit(uri)
        except UnicodeError:
            self.simple_response('400 Bad Request', 'Malformed Request-URI')
            return False

        if self.method == b'OPTIONS':
            # TODO: cover this branch with tests
            path = (uri
                    # https://tools.ietf.org/html/rfc7230#section-5.3.4
                    if self.proxy_mode or uri == ASTERISK
                    else path)
        elif self.method == b'CONNECT':
            # TODO: cover this branch with tests
            if not self.proxy_mode:
                self.simple_response('405 Method Not Allowed')
                return False

            # `urlsplit()` above parses "example.com:3128" as path part of URI.
            # this is a workaround, which makes it detect netloc correctly
            uri_split = urllib.parse.urlsplit(b'//' + uri)
            _scheme, _authority, _path, _qs, _fragment = uri_split
            _port = EMPTY
            try:
                _port = uri_split.port
            except ValueError:
                pass

            # FIXME: use third-party validation to make checks against RFC
            # the validation doesn't take into account, that urllib parses
            # invalid URIs without raising errors
            # https://tools.ietf.org/html/rfc7230#section-5.3.3
            invalid_path = (
                _authority != uri
                or not _port
                or any((_scheme, _path, _qs, _fragment))
            )
            if invalid_path:
                self.simple_response('400 Bad Request',
                                     'Invalid path in Request-URI: request-'
                                     'target must match authority-form.')
                return False

            authority = path = _authority
            scheme = qs = fragment = EMPTY
        else:
            uri_is_absolute_form = (scheme or authority)

            disallowed_absolute = (
                self.strict_mode
                and not self.proxy_mode
                and uri_is_absolute_form
            )
            if disallowed_absolute:
                # https://tools.ietf.org/html/rfc7230#section-5.3.2
                # (absolute form)
                """Absolute URI is only allowed within proxies."""
                self.simple_response(
                    '400 Bad Request',
                    'Absolute URI not allowed if server is not a proxy.',
                )
                return False

            invalid_path = (
                self.strict_mode
                and not uri.startswith(FORWARD_SLASH)
                and not uri_is_absolute_form
            )
            if invalid_path:
                # https://tools.ietf.org/html/rfc7230#section-5.3.1
                # (origin_form) and
                """Path should start with a forward slash."""
                resp = (
                    'Invalid path in Request-URI: request-target must contain '
                    'origin-form which starts with absolute-path (URI '
                    'starting with a slash "/").'
                )
                self.simple_response('400 Bad Request', resp)
                return False

            if fragment:
                self.simple_response('400 Bad Request',
                                     'Illegal #fragment in Request-URI.')
                return False

            if path is None:
                # FIXME: It looks like this case cannot happen
                self.simple_response('400 Bad Request',
                                     'Invalid path in Request-URI.')
                return False

            # Unquote the path+params (e.g. "/this%20path" -> "/this path").
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html#sec5.1.2
            #
            # But note that "...a URI must be separated into its components
            # before the escaped characters within those components can be
            # safely decoded." http://www.ietf.org/rfc/rfc2396.txt, sec 2.4.2
            # Therefore, "/this%2Fpath" becomes "/this%2Fpath", not
            # "/this/path".
            try:
                # TODO: Figure out whether exception can really happen here.
                # It looks like it's caught on urlsplit() call above.
                atoms = [
                    urllib.parse.unquote_to_bytes(x)
                    for x in QUOTED_SLASH_REGEX.split(path)
                ]
            except ValueError as ex:
                self.simple_response('400 Bad Request', ex.args[0])
                return False
            path = QUOTED_SLASH.join(atoms)

        if not path.startswith(FORWARD_SLASH):
            path = FORWARD_SLASH + path

        if scheme is not EMPTY:
            self.scheme = scheme
        self.authority = authority
        self.path = path

        # Note that, like wsgiref and most other HTTP servers,
        # we "% HEX HEX"-unquote the path but not the query string.
        self.qs = qs

        # Compare request and server HTTP protocol versions, in case our
        # server does not support the requested protocol. Limit our output
        # to min(req, server). We want the following output:
        #     request    server     actual written   supported response
        #     protocol   protocol  response protocol    feature set
        # a     1.0        1.0           1.0                1.0
        # b     1.0        1.1           1.1                1.0
        # c     1.1        1.0           1.0                1.0
        # d     1.1        1.1           1.1                1.1
        # Notice that, in (b), the response will be "HTTP/1.1" even though
        # the client only understands 1.0. RFC 2616 10.5.6 says we should
        # only return 505 if the _major_ version is different.
        sp = int(self.server.protocol[5]), int(self.server.protocol[7])

        if sp[0] != rp[0]:
            self.simple_response('505 HTTP Version Not Supported')
            return False

        self.request_protocol = req_protocol
        self.response_protocol = 'HTTP/%s.%s' % min(rp, sp)

        return True

    def read_request_headers(self):
        """Read self.rfile into self.inheaders. Return success."""
        # then all the http headers
        try:
            self.header_reader(self.rfile, self.inheaders)
        except ValueError as ex:
            self.simple_response('400 Bad Request', ex.args[0])
            return False

        mrbs = self.server.max_request_body_size
        if mrbs and int(self.inheaders.get(b'Content-Length', 0)) > mrbs:
            self.simple_response(
                '413 Request Entity Too Large',
                'The entity sent with the request exceeds the maximum '
                'allowed bytes.')
            return False

        # Persistent connection support
        if self.response_protocol == 'HTTP/1.1':
            # Both server and client are HTTP/1.1
            if self.inheaders.get(b'Connection', b'') == b'close':
                self.close_connection = True
        else:
            # Either the server or client (or both) are HTTP/1.0
            if self.inheaders.get(b'Connection', b'') != b'Keep-Alive':
                self.close_connection = True

        # Transfer-Encoding support
        te = None
        if self.response_protocol == 'HTTP/1.1':
            te = self.inheaders.get(b'Transfer-Encoding')
            if te:
                te = [x.strip().lower() for x in te.split(b',') if x.strip()]

        self.chunked_read = False

        if te:
            for enc in te:
                if enc == b'chunked':
                    self.chunked_read = True
                else:
                    # Note that, even if we see "chunked", we must reject
                    # if there is an extension we don't recognize.
                    self.simple_response('501 Unimplemented')
                    self.close_connection = True
                    return False

        # From PEP 333:
        # "Servers and gateways that implement HTTP 1.1 must provide
        # transparent support for HTTP 1.1's "expect/continue" mechanism.
        # This may be done in any of several ways:
        #   1. Respond to requests containing an Expect: 100-continue request
        #      with an immediate "100 Continue" response, and proceed normally.
        #   2. Proceed with the request normally, but provide the application
        #      with a wsgi.input stream that will send the "100 Continue"
        #      response if/when the application first attempts to read from
        #      the input stream. The read request must then remain blocked
        #      until the client responds.
        #   3. Wait until the client decides that the server does not support
        #      expect/continue, and sends the request body on its own.
        #      (This is suboptimal, and is not recommended.)
        #
        # We used to do 3, but are now doing 1. Maybe we'll do 2 someday,
        # but it seems like it would be a big slowdown for such a rare case.
        if self.inheaders.get(b'Expect', b'') == b'100-continue':
            # Don't use simple_response here, because it emits headers
            # we don't want. See
            # https://github.com/cherrypy/cherrypy/issues/951
            msg = self.server.protocol.encode('ascii')
            msg += b' 100 Continue\r\n\r\n'
            try:
                self.conn.wfile.write(msg)
            except socket.error as ex:
                if ex.args[0] not in errors.socket_errors_to_ignore:
                    raise
        return True

    def respond(self):
        """Call the gateway and write its iterable output."""
        mrbs = self.server.max_request_body_size
        if self.chunked_read:
            self.rfile = ChunkedRFile(self.conn.rfile, mrbs)
        else:
            cl = int(self.inheaders.get(b'Content-Length', 0))
            if mrbs and mrbs < cl:
                if not self.sent_headers:
                    self.simple_response(
                        '413 Request Entity Too Large',
                        'The entity sent with the request exceeds the '
                        'maximum allowed bytes.')
                return
            self.rfile = KnownLengthRFile(self.conn.rfile, cl)

        self.server.gateway(self).respond()

        if (self.ready and not self.sent_headers):
            self.sent_headers = True
            self.send_headers()
        if self.chunked_write:
            self.conn.wfile.write(b'0\r\n\r\n')

    def simple_response(self, status, msg=''):
        """Write a simple response back to the client."""
        status = str(status)
        proto_status = '%s %s\r\n' % (self.server.protocol, status)
        content_length = 'Content-Length: %s\r\n' % len(msg)
        content_type = 'Content-Type: text/plain\r\n'
        buf = [
            proto_status.encode('ISO-8859-1'),
            content_length.encode('ISO-8859-1'),
            content_type.encode('ISO-8859-1'),
        ]

        if status[:3] in ('413', '414'):
            # Request Entity Too Large / Request-URI Too Long
            self.close_connection = True
            if self.response_protocol == 'HTTP/1.1':
                # This will not be true for 414, since read_request_line
                # usually raises 414 before reading the whole line, and we
                # therefore cannot know the proper response_protocol.
                buf.append(b'Connection: close\r\n')
            else:
                # HTTP/1.0 had no 413/414 status nor Connection header.
                # Emit 400 instead and trust the message body is enough.
                status = '400 Bad Request'

        buf.append(CRLF)
        if msg:
            if isinstance(msg, six.text_type):
                msg = msg.encode('ISO-8859-1')
            buf.append(msg)

        try:
            self.conn.wfile.write(EMPTY.join(buf))
        except socket.error as ex:
            if ex.args[0] not in errors.socket_errors_to_ignore:
                raise

    def write(self, chunk):
        """Write unbuffered data to the client."""
        if self.chunked_write and chunk:
            chunk_size_hex = hex(len(chunk))[2:].encode('ascii')
            buf = [chunk_size_hex, CRLF, chunk, CRLF]
            self.conn.wfile.write(EMPTY.join(buf))
        else:
            self.conn.wfile.write(chunk)

    def send_headers(self):
        """Assert, process, and send the HTTP response message-headers.

        You must set self.status, and self.outheaders before calling this.
        """
        hkeys = [key.lower() for key, value in self.outheaders]
        status = int(self.status[:3])

        if status == 413:
            # Request Entity Too Large. Close conn to avoid garbage.
            self.close_connection = True
        elif b'content-length' not in hkeys:
            # "All 1xx (informational), 204 (no content),
            # and 304 (not modified) responses MUST NOT
            # include a message-body." So no point chunking.
            if status < 200 or status in (204, 205, 304):
                pass
            else:
                needs_chunked = (
                    self.response_protocol == 'HTTP/1.1'
                    and self.method != b'HEAD'
                )
                if needs_chunked:
                    # Use the chunked transfer-coding
                    self.chunked_write = True
                    self.outheaders.append((b'Transfer-Encoding', b'chunked'))
                else:
                    # Closing the conn is the only way to determine len.
                    self.close_connection = True

        if b'connection' not in hkeys:
            if self.response_protocol == 'HTTP/1.1':
                # Both server and client are HTTP/1.1 or better
                if self.close_connection:
                    self.outheaders.append((b'Connection', b'close'))
            else:
                # Server and/or client are HTTP/1.0
                if not self.close_connection:
                    self.outheaders.append((b'Connection', b'Keep-Alive'))

        if (not self.close_connection) and (not self.chunked_read):
            # Read any remaining request body data on the socket.
            # "If an origin server receives a request that does not include an
            # Expect request-header field with the "100-continue" expectation,
            # the request includes a request body, and the server responds
            # with a final status code before reading the entire request body
            # from the transport connection, then the server SHOULD NOT close
            # the transport connection until it has read the entire request,
            # or until the client closes the connection. Otherwise, the client
            # might not reliably receive the response message. However, this
            # requirement is not be construed as preventing a server from
            # defending itself against denial-of-service attacks, or from
            # badly broken client implementations."
            remaining = getattr(self.rfile, 'remaining', 0)
            if remaining > 0:
                self.rfile.read(remaining)

        if b'date' not in hkeys:
            self.outheaders.append((
                b'Date',
                email.utils.formatdate(usegmt=True).encode('ISO-8859-1'),
            ))

        if b'server' not in hkeys:
            self.outheaders.append((
                b'Server',
                self.server.server_name.encode('ISO-8859-1'),
            ))

        proto = self.server.protocol.encode('ascii')
        buf = [proto + SPACE + self.status + CRLF]
        for k, v in self.outheaders:
            buf.append(k + COLON + SPACE + v + CRLF)
        buf.append(CRLF)
        self.conn.wfile.write(EMPTY.join(buf))


class HTTPConnection(object):
    """An HTTP connection (active socket)."""

    remote_addr = None
    remote_port = None
    ssl_env = None
    rbufsize = io.DEFAULT_BUFFER_SIZE
    wbufsize = io.DEFAULT_BUFFER_SIZE
    RequestHandlerClass = HTTPRequest

    def __init__(self, server, sock, makefile=MakeFile):
        """Initialize HTTPConnection instance.

        Args:
            server (HTTPServer): web server object receiving this request
            socket (socket._socketobject): the raw socket object (usually
                TCP) for this connection
            makefile (file): a fileobject class for reading from the socket
        """
        self.server = server
        self.socket = sock
        self.rfile = makefile(sock, 'rb', self.rbufsize)
        self.wfile = makefile(sock, 'wb', self.wbufsize)
        self.requests_seen = 0

    def communicate(self):
        """Read each request and respond appropriately."""
        request_seen = False
        try:
            while True:
                # (re)set req to None so that if something goes wrong in
                # the RequestHandlerClass constructor, the error doesn't
                # get written to the previous request.
                req = None
                req = self.RequestHandlerClass(self.server, self)

                # This order of operations should guarantee correct pipelining.
                req.parse_request()
                if self.server.stats['Enabled']:
                    self.requests_seen += 1
                if not req.ready:
                    # Something went wrong in the parsing (and the server has
                    # probably already made a simple_response). Return and
                    # let the conn close.
                    return

                request_seen = True
                req.respond()
                if req.close_connection:
                    return
        except socket.error as ex:
            errnum = ex.args[0]
            # sadly SSL sockets return a different (longer) time out string
            timeout_errs = 'timed out', 'The read operation timed out'
            if errnum in timeout_errs:
                # Don't error if we're between requests; only error
                # if 1) no request has been started at all, or 2) we're
                # in the middle of a request.
                # See https://github.com/cherrypy/cherrypy/issues/853
                if (not request_seen) or (req and req.started_request):
                    self._conditional_error(req, '408 Request Timeout')
            elif errnum not in errors.socket_errors_to_ignore:
                self.server.error_log('socket.error %s' % repr(errnum),
                                      level=logging.WARNING, traceback=True)
                self._conditional_error(req, '500 Internal Server Error')
        except (KeyboardInterrupt, SystemExit):
            raise
        except errors.FatalSSLAlert:
            pass
        except errors.NoSSLError:
            self._handle_no_ssl(req)
        except Exception as ex:
            self.server.error_log(
                repr(ex), level=logging.ERROR, traceback=True)
            self._conditional_error(req, '500 Internal Server Error')

    linger = False

    def _handle_no_ssl(self, req):
        if not req or req.sent_headers:
            return
        # Unwrap wfile
        self.wfile = MakeFile(self.socket._sock, 'wb', self.wbufsize)
        msg = (
            'The client sent a plain HTTP request, but '
            'this server only speaks HTTPS on this port.'
        )
        req.simple_response('400 Bad Request', msg)
        self.linger = True

    def _conditional_error(self, req, response):
        """Respond with an error.

        Don't bother writing if a response
        has already started being written.
        """
        if not req or req.sent_headers:
            return

        try:
            req.simple_response('408 Request Timeout')
        except errors.FatalSSLAlert:
            pass
        except errors.NoSSLError:
            self._handle_no_ssl(req)

    def close(self):
        """Close the socket underlying this connection."""
        self.rfile.close()

        if not self.linger:
            self._close_kernel_socket()
            self.socket.close()
        else:
            # On the other hand, sometimes we want to hang around for a bit
            # to make sure the client has a chance to read our entire
            # response. Skipping the close() calls here delays the FIN
            # packet until the socket object is garbage-collected later.
            # Someday, perhaps, we'll do the full lingering_close that
            # Apache does, but not today.
            pass

    def _close_kernel_socket(self):
        """Close kernel socket in outdated Python versions.

        On old Python versions,
        Python's socket module does NOT call close on the kernel
        socket when you call socket.close(). We do so manually here
        because we want this server to send a FIN TCP segment
        immediately. Note this must be called *before* calling
        socket.close(), because the latter drops its reference to
        the kernel socket.
        """
        if six.PY2 and hasattr(self.socket, '_sock'):
            self.socket._sock.close()


try:
    import fcntl
except ImportError:
    try:
        from ctypes import windll, WinError
        import ctypes.wintypes
        _SetHandleInformation = windll.kernel32.SetHandleInformation
        _SetHandleInformation.argtypes = [
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
        ]
        _SetHandleInformation.restype = ctypes.wintypes.BOOL
    except ImportError:
        def prevent_socket_inheritance(sock):
            """Dummy function, since neither fcntl nor ctypes are available."""
            pass
    else:
        def prevent_socket_inheritance(sock):
            """Mark the given socket fd as non-inheritable (Windows)."""
            if not _SetHandleInformation(sock.fileno(), 1, 0):
                raise WinError()
else:
    def prevent_socket_inheritance(sock):
        """Mark the given socket fd as non-inheritable (POSIX)."""
        fd = sock.fileno()
        old_flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFD, old_flags | fcntl.FD_CLOEXEC)


class HTTPServer(object):
    """An HTTP server."""

    _bind_addr = '127.0.0.1'
    _interrupt = None

    gateway = None
    """A Gateway instance."""

    minthreads = None
    """The minimum number of worker threads to create (default 10)."""

    maxthreads = None
    """The maximum number of worker threads to create.

    (default -1 = no limit)"""

    server_name = None
    """The name of the server; defaults to ``self.version``."""

    protocol = 'HTTP/1.1'
    """The version string to write in the Status-Line of all HTTP responses.

    For example, "HTTP/1.1" is the default. This also limits the supported
    features used in the response."""

    request_queue_size = 5
    """The 'backlog' arg to socket.listen(); max queued connections.

    (default 5)."""

    shutdown_timeout = 5
    """The total time to wait for worker threads to cleanly exit.

    Specified in seconds."""

    timeout = 10
    """The timeout in seconds for accepted connections (default 10)."""

    version = 'Cheroot/' + __version__
    """A version string for the HTTPServer."""

    software = None
    """The value to set for the SERVER_SOFTWARE entry in the WSGI environ.

    If None, this defaults to ``'%s Server' % self.version``.
    """

    ready = False
    """Internal flag which indicating the socket is accepting connections."""

    max_request_header_size = 0
    """The maximum size, in bytes, for request headers, or 0 for no limit."""

    max_request_body_size = 0
    """The maximum size, in bytes, for request bodies, or 0 for no limit."""

    nodelay = True
    """If True (the default since 3.1), sets the TCP_NODELAY socket option."""

    ConnectionClass = HTTPConnection
    """The class to use for handling HTTP connections."""

    ssl_adapter = None
    """An instance of ssl.Adapter (or a subclass).

    You must have the corresponding SSL driver library installed.
    """

    def __init__(
            self, bind_addr, gateway, minthreads=10, maxthreads=-1,
            server_name=None):
        """Initialize HTTPServer instance.

        Args:
            bind_addr (tuple): network interface to listen to
            gateway (Gateway): gateway for processing HTTP requests
            minthreads (int): minimum number of threads for HTTP thread pool
            maxthreads (int): maximum number of threads for HTTP thread pool
            server_name (str): web server name to be advertised via Server
                HTTP header
        """
        self.bind_addr = bind_addr
        self.gateway = gateway

        self.requests = threadpool.ThreadPool(
            self, min=minthreads or 1, max=maxthreads)

        if not server_name:
            server_name = self.version
        self.server_name = server_name
        self.clear_stats()

    def clear_stats(self):
        """Reset server stat counters.."""
        self._start_time = None
        self._run_time = 0
        self.stats = {
            'Enabled': False,
            'Bind Address': lambda s: repr(self.bind_addr),
            'Run time': lambda s: (not s['Enabled']) and -1 or self.runtime(),
            'Accepts': 0,
            'Accepts/sec': lambda s: s['Accepts'] / self.runtime(),
            'Queue': lambda s: getattr(self.requests, 'qsize', None),
            'Threads': lambda s: len(getattr(self.requests, '_threads', [])),
            'Threads Idle': lambda s: getattr(self.requests, 'idle', None),
            'Socket Errors': 0,
            'Requests': lambda s: (not s['Enabled']) and -1 or sum(
                [w['Requests'](w) for w in s['Worker Threads'].values()], 0),
            'Bytes Read': lambda s: (not s['Enabled']) and -1 or sum(
                [w['Bytes Read'](w) for w in s['Worker Threads'].values()], 0),
            'Bytes Written': lambda s: (not s['Enabled']) and -1 or sum(
                [w['Bytes Written'](w) for w in s['Worker Threads'].values()],
                0),
            'Work Time': lambda s: (not s['Enabled']) and -1 or sum(
                [w['Work Time'](w) for w in s['Worker Threads'].values()], 0),
            'Read Throughput': lambda s: (not s['Enabled']) and -1 or sum(
                [w['Bytes Read'](w) / (w['Work Time'](w) or 1e-6)
                 for w in s['Worker Threads'].values()], 0),
            'Write Throughput': lambda s: (not s['Enabled']) and -1 or sum(
                [w['Bytes Written'](w) / (w['Work Time'](w) or 1e-6)
                 for w in s['Worker Threads'].values()], 0),
            'Worker Threads': {},
        }
        logging.statistics['Cheroot HTTPServer %d' % id(self)] = self.stats

    def runtime(self):
        """Return server uptime."""
        if self._start_time is None:
            return self._run_time
        else:
            return self._run_time + (time.time() - self._start_time)

    def __str__(self):
        """Render Server instance representing bind address."""
        return '%s.%s(%r)' % (self.__module__, self.__class__.__name__,
                              self.bind_addr)

    def _get_bind_addr(self):
        return self._bind_addr

    def _set_bind_addr(self, value):
        if isinstance(value, tuple) and value[0] in ('', None):
            # Despite the socket module docs, using '' does not
            # allow AI_PASSIVE to work. Passing None instead
            # returns '0.0.0.0' like we want. In other words:
            #     host    AI_PASSIVE     result
            #      ''         Y         192.168.x.y
            #      ''         N         192.168.x.y
            #     None        Y         0.0.0.0
            #     None        N         127.0.0.1
            # But since you can get the same effect with an explicit
            # '0.0.0.0', we deny both the empty string and None as values.
            raise ValueError("Host values of '' or None are not allowed. "
                             "Use '0.0.0.0' (IPv4) or '::' (IPv6) instead "
                             'to listen on all active interfaces.')
        self._bind_addr = value
    bind_addr = property(
        _get_bind_addr,
        _set_bind_addr,
        doc="""The interface on which to listen for connections.

        For TCP sockets, a (host, port) tuple. Host values may be any IPv4
        or IPv6 address, or any valid hostname. The string 'localhost' is a
        synonym for '127.0.0.1' (or '::1', if your hosts file prefers IPv6).
        The string '0.0.0.0' is a special IPv4 entry meaning "any active
        interface" (INADDR_ANY), and '::' is the similar IN6ADDR_ANY for
        IPv6. The empty string or None are not allowed.

        For UNIX sockets, supply the filename as a string.

        Systemd socket activation is automatic and doesn't require tempering
        with this variable""")

    def safe_start(self):
        """Run the server forever, and stop it cleanly on exit."""
        try:
            self.start()
        except (KeyboardInterrupt, IOError):
            # The time.sleep call might raise
            # "IOError: [Errno 4] Interrupted function call" on KBInt.
            self.error_log('Keyboard Interrupt: shutting down')
            self.stop()
            raise
        except SystemExit:
            self.error_log('SystemExit raised: shutting down')
            self.stop()
            raise

    def start(self):
        """Run the server forever."""
        # We don't have to trap KeyboardInterrupt or SystemExit here,
        # because cherrpy.server already does so, calling self.stop() for us.
        # If you're using this server with another framework, you should
        # trap those exceptions in whatever code block calls start().
        self._interrupt = None

        if self.software is None:
            self.software = '%s Server' % self.version

        # Select the appropriate socket
        self.socket = None
        if os.getenv('LISTEN_PID', None):
            # systemd socket activation
            self.socket = socket.fromfd(3, socket.AF_INET, socket.SOCK_STREAM)
        elif isinstance(self.bind_addr, six.string_types):
            # AF_UNIX socket

            # So we can reuse the socket...
            try:
                os.unlink(self.bind_addr)
            except Exception:
                pass

            # So everyone can access the socket...
            try:
                os.chmod(self.bind_addr, 0o777)
            except Exception:
                pass

            info = [
                (socket.AF_UNIX, socket.SOCK_STREAM, 0, '', self.bind_addr)]
        else:
            # AF_INET or AF_INET6 socket
            # Get the correct address family for our host (allows IPv6
            # addresses)
            host, port = self.bind_addr
            try:
                info = socket.getaddrinfo(
                    host, port, socket.AF_UNSPEC,
                    socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
            except socket.gaierror:
                if ':' in self.bind_addr[0]:
                    info = [(socket.AF_INET6, socket.SOCK_STREAM,
                             0, '', self.bind_addr + (0, 0))]
                else:
                    info = [(socket.AF_INET, socket.SOCK_STREAM,
                             0, '', self.bind_addr)]

        if not self.socket:
            msg = 'No socket could be created'
            for res in info:
                af, socktype, proto, canonname, sa = res
                try:
                    self.bind(af, socktype, proto)
                    break
                except socket.error as serr:
                    msg = '%s -- (%s: %s)' % (msg, sa, serr)
                    if self.socket:
                        self.socket.close()
                    self.socket = None

            if not self.socket:
                raise socket.error(msg)

        # Timeout so KeyboardInterrupt can be caught on Win32
        self.socket.settimeout(1)
        self.socket.listen(self.request_queue_size)

        # Create worker threads
        self.requests.start()

        self.ready = True
        self._start_time = time.time()
        while self.ready:
            try:
                self.tick()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                self.error_log('Error in HTTPServer.tick', level=logging.ERROR,
                               traceback=True)

            if self.interrupt:
                while self.interrupt is True:
                    # Wait for self.stop() to complete. See _set_interrupt.
                    time.sleep(0.1)
                if self.interrupt:
                    raise self.interrupt

    def error_log(self, msg='', level=20, traceback=False):
        """Write error message to log.

        Args:
            msg (str): error message
            level (int): logging level
            traceback (bool): add traceback to output or not
        """
        # Override this in subclasses as desired
        sys.stderr.write(msg + '\n')
        sys.stderr.flush()
        if traceback:
            tblines = traceback_.format_exc()
            sys.stderr.write(tblines)
            sys.stderr.flush()

    def bind(self, family, type, proto=0):
        """Create (or recreate) the actual socket object."""
        self.socket = socket.socket(family, type, proto)
        prevent_socket_inheritance(self.socket)
        if platform.system() != 'Windows':
            # Windows has different semantics for SO_REUSEADDR,
            # so don't set it.
            # https://msdn.microsoft.com/en-us/library/ms740621(v=vs.85).aspx
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.nodelay and not isinstance(self.bind_addr, str):
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        if self.ssl_adapter is not None:
            self.socket = self.ssl_adapter.bind(self.socket)

        host, port = self.bind_addr[:2]

        # If listening on the IPV6 any address ('::' = IN6ADDR_ANY),
        # activate dual-stack. See
        # https://github.com/cherrypy/cherrypy/issues/871.
        listening_ipv6 = (
            hasattr(socket, 'AF_INET6')
            and family == socket.AF_INET6
            and host in ('::', '::0', '::0.0.0.0')
        )
        if listening_ipv6:
            try:
                self.socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            except (AttributeError, socket.error):
                # Apparently, the socket option is not available in
                # this machine's TCP stack
                pass

        self.socket.bind(self.bind_addr)

    def tick(self):
        """Accept a new connection and put it on the Queue."""
        try:
            s, addr = self.socket.accept()
            if self.stats['Enabled']:
                self.stats['Accepts'] += 1
            if not self.ready:
                return

            prevent_socket_inheritance(s)
            if hasattr(s, 'settimeout'):
                s.settimeout(self.timeout)

            mf = MakeFile
            ssl_env = {}
            # if ssl cert and key are set, we try to be a secure HTTP server
            if self.ssl_adapter is not None:
                try:
                    s, ssl_env = self.ssl_adapter.wrap(s)
                except errors.NoSSLError:
                    msg = ('The client sent a plain HTTP request, but '
                           'this server only speaks HTTPS on this port.')
                    buf = ['%s 400 Bad Request\r\n' % self.protocol,
                           'Content-Length: %s\r\n' % len(msg),
                           'Content-Type: text/plain\r\n\r\n',
                           msg]

                    sock_to_make = s if six.PY3 else s._sock
                    wfile = mf(sock_to_make, 'wb', io.DEFAULT_BUFFER_SIZE)
                    try:
                        wfile.write(''.join(buf).encode('ISO-8859-1'))
                    except socket.error as ex:
                        if ex.args[0] not in errors.socket_errors_to_ignore:
                            raise
                    return
                if not s:
                    return
                mf = self.ssl_adapter.makefile
                # Re-apply our timeout since we may have a new socket object
                if hasattr(s, 'settimeout'):
                    s.settimeout(self.timeout)

            conn = self.ConnectionClass(self, s, mf)

            if not isinstance(self.bind_addr, six.string_types):
                # optional values
                # Until we do DNS lookups, omit REMOTE_HOST
                if addr is None:  # sometimes this can happen
                    # figure out if AF_INET or AF_INET6.
                    if len(s.getsockname()) == 2:
                        # AF_INET
                        addr = ('0.0.0.0', 0)
                    else:
                        # AF_INET6
                        addr = ('::', 0)
                conn.remote_addr = addr[0]
                conn.remote_port = addr[1]

            conn.ssl_env = ssl_env

            try:
                self.requests.put(conn)
            except queue.Full:
                # Just drop the conn. TODO: write 503 back?
                conn.close()
                return
        except socket.timeout:
            # The only reason for the timeout in start() is so we can
            # notice keyboard interrupts on Win32, which don't interrupt
            # accept() by default
            return
        except socket.error as ex:
            if self.stats['Enabled']:
                self.stats['Socket Errors'] += 1
            if ex.args[0] in errors.socket_error_eintr:
                # I *think* this is right. EINTR should occur when a signal
                # is received during the accept() call; all docs say retry
                # the call, and I *think* I'm reading it right that Python
                # will then go ahead and poll for and handle the signal
                # elsewhere. See
                # https://github.com/cherrypy/cherrypy/issues/707.
                return
            if ex.args[0] in errors.socket_errors_nonblocking:
                # Just try again. See
                # https://github.com/cherrypy/cherrypy/issues/479.
                return
            if ex.args[0] in errors.socket_errors_to_ignore:
                # Our socket was closed.
                # See https://github.com/cherrypy/cherrypy/issues/686.
                return
            raise

    def _get_interrupt(self):
        return self._interrupt

    def _set_interrupt(self, interrupt):
        self._interrupt = True
        self.stop()
        self._interrupt = interrupt
    interrupt = property(_get_interrupt, _set_interrupt,
                         doc='Set this to an Exception instance to '
                             'interrupt the server.')

    def stop(self):
        """Gracefully shutdown a server that is serving forever."""
        self.ready = False
        if self._start_time is not None:
            self._run_time += (time.time() - self._start_time)
        self._start_time = None

        sock = getattr(self, 'socket', None)
        if sock:
            if not isinstance(self.bind_addr, six.string_types):
                # Touch our own socket to make accept() return immediately.
                try:
                    host, port = sock.getsockname()[:2]
                except socket.error as ex:
                    if ex.args[0] not in errors.socket_errors_to_ignore:
                        # Changed to use error code and not message
                        # See
                        # https://github.com/cherrypy/cherrypy/issues/860.
                        raise
                else:
                    # Note that we're explicitly NOT using AI_PASSIVE,
                    # here, because we want an actual IP to touch.
                    # localhost won't work if we've bound to a public IP,
                    # but it will if we bound to '0.0.0.0' (INADDR_ANY).
                    for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                                  socket.SOCK_STREAM):
                        af, socktype, proto, canonname, sa = res
                        s = None
                        try:
                            s = socket.socket(af, socktype, proto)
                            # See
                            # http://groups.google.com/group/cherrypy-users/
                            #     browse_frm/thread/bbfe5eb39c904fe0
                            s.settimeout(1.0)
                            s.connect((host, port))
                            s.close()
                        except socket.error:
                            if s:
                                s.close()
            if hasattr(sock, 'close'):
                sock.close()
            self.socket = None

        self.requests.stop(self.shutdown_timeout)


class Gateway(object):
    """Base class to interface HTTPServer with other systems, such as WSGI."""

    def __init__(self, req):
        """Initialize Gateway instance with request.

        Args:
            req (HTTPRequest): current HTTP request
        """
        self.req = req

    def respond(self):
        """Process the current request. Must be overridden in a subclass."""
        raise NotImplementedError


# These may either be ssl.Adapter subclasses or the string names
# of such classes (in which case they will be lazily loaded).
ssl_adapters = {
    'builtin': 'cheroot.ssl.builtin.BuiltinSSLAdapter',
    'pyopenssl': 'cheroot.ssl.pyopenssl.pyOpenSSLAdapter',
}


def get_ssl_adapter_class(name='builtin'):
    """Return an SSL adapter class for the given name."""
    adapter = ssl_adapters[name.lower()]
    if isinstance(adapter, six.string_types):
        last_dot = adapter.rfind('.')
        attr_name = adapter[last_dot + 1:]
        mod_path = adapter[:last_dot]

        try:
            mod = sys.modules[mod_path]
            if mod is None:
                raise KeyError()
        except KeyError:
            # The last [''] is important.
            mod = __import__(mod_path, globals(), locals(), [''])

        # Let an AttributeError propagate outward.
        try:
            adapter = getattr(mod, attr_name)
        except AttributeError:
            raise AttributeError("'%s' object has no attribute '%s'"
                                 % (mod_path, attr_name))

    return adapter
