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

_GLOBAL_DEFAULT_TIMEOUT = object()
def create_connection(address, timeout=_GLOBAL_DEFAULT_TIMEOUT):
    """Connect to *address* and return the socket object.

    Convenience function.  Connect to *address* (a 2-tuple ``(host,
    port)``) and return the socket object.  Passing the optional
    *timeout* parameter will set the timeout on the socket instance
    before attempting to connect.  If no *timeout* is supplied, the
    global default timeout setting returned by :func:`getdefaulttimeout`
    is used.
    """

    msg = "getaddrinfo returns an empty list"
    host, port = address
    for res in getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket(af, socktype, proto)
            if timeout is not _GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            sock.connect(sa)
            return sock

        except error, msg:
            if sock is not None:
                sock.close()

    raise error, msg
    
class ClickAndLoad(Hook):
    __name__    = "ClickAndLoad"
    __type__    = "hook"
    __version__ = "0.27"

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
            self.server(ip, webport, cnlport)

        finally:
            dock_socket.close()
