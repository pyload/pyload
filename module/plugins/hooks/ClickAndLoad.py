# -*- coding: utf-8 -*-

import socket

from threading import Thread, Lock
from time import sleep

from module.plugins.Hook import Hook, threaded


def forward(source, destination):
    string = ' '
    while string:
        string = source.recv(1024)
        if string:
            destination.sendall(string)
        else:
            destination.shutdown(socket.SHUT_WR)


#: socket.create_connection wrapper for python 2.5
def create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):
    try:
        return socket.create_connection(address, timeout, source_address)

    except SyntaxError:
        """Connect to *address* and return the socket object.

        Convenience function.  Connect to *address* (a 2-tuple ``(host,
        port)``) and return the socket object.  Passing the optional
        *timeout* parameter will set the timeout on the socket instance
        before attempting to connect.  If no *timeout* is supplied, the
        global default timeout setting returned by :func:`getdefaulttimeout`
        is used.  If *source_address* is set it must be a tuple of (host, port)
        for the socket to bind as a source address before making the connection.
        An host of \'\' or port 0 tells the OS to use the default.
        """

        host, port = address
        err = None
        for res in getaddrinfo(host, port, 0, SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            sock = None
            try:
                sock = socket(af, socktype, proto)
                if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                    sock.settimeout(timeout)
                if source_address:
                    sock.bind(source_address)
                sock.connect(sa)
                return sock

            except error as _:
                err = _
                if sock is not None:
                    sock.close()

        if err is not None:
            raise err
        else:
            raise error("getaddrinfo returns an empty list")


class ClickAndLoad(Hook):
    __name__    = "ClickAndLoad"
    __type__    = "hook"
    __version__ = "0.28"

    __config__ = [("activated", "bool", "Activated"                                     , True ),
                  ("port"     , "int" , "Port"                                          , 9666 ),
                  ("extern"   , "bool", "Listen for requests coming from WAN (internet)", False)]

    __description__ = """Click'N'Load hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def coreReady(self):
        if not self.config['webinterface']['activated']:
            return

        ip      = "0.0.0.0" if self.getConfig("extern") else "127.0.0.1"
        webport = int(self.config['webinterface']['port'])
        cnlport = self.getConfig('port')

        self.proxy(ip, webport, cnlport)


    @threaded
    def proxy(self, ip, webport, cnlport):
        hookManager.startThread(self.server, ip, webport, cnlport)
        lock = Lock()
        lock.acquire()
        lock.acquire()


    def server(self, ip, webport, cnlport):
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            dock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            dock_socket.bind((ip, cnlport))
            dock_socket.listen(5)

            while True:
                server_socket = dock_socket.accept()[0]
                client_socket = create_connection(("127.0.0.1", webport))

                hookManager.startThread(forward, server_socket, client_socket)
                hookManager.startThread(forward, client_socket, server_socket)

        except socket.error, e:
            self.logError(e)

        finally:
            dock_socket.close()
