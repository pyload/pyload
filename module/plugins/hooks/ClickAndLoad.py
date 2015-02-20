# -*- coding: utf-8 -*-

import socket
import time

from threading import Lock

from module.plugins.Hook import Hook, threaded


def forward(source, destination):
    try:
        bufsize = 1024
        bufdata = source.recv(bufsize)
        while bufdata:
            destination.sendall(bufdata)
            bufdata = source.recv(bufsize)
    finally:
        destination.shutdown(socket.SHUT_WR)


#@TODO: IPv6 support
class ClickAndLoad(Hook):
    __name__    = "ClickAndLoad"
    __type__    = "hook"
    __version__ = "0.37"

    __config__ = [("activated", "bool", "Activated"                             , True),
                  ("port"     , "int" , "Port"                                  , 9666),
                  ("extern"   , "bool", "Listen on the public network interface", True)]

    __description__ = """Click'N'Load hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def coreReady(self):
        if not self.config['webinterface']['activated']:
            return

        ip      = "" if self.getConfig("extern") else "127.0.0.1"
        webport = int(self.config['webinterface']['port'])
        cnlport = self.getConfig('port')

        self.proxy(ip, webport, cnlport)


    @threaded
    def proxy(self, ip, webport, cnlport):
        self.logInfo(_("Proxy listening on %s:%s") % (ip, cnlport))
        self.manager.startThread(self._server, ip, webport, cnlport)
        lock = Lock()
        lock.acquire()
        lock.acquire()


    def _server(self, ip, webport, cnlport, thread):
        try:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                server_socket.bind((ip, cnlport))
                server_socket.listen(5)

                while True:
                    client_socket = server_socket.accept()[0]
                    dock_socket   = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    dock_socket.connect(("127.0.0.1", webport))

                    self.manager.startThread(forward, dock_socket, client_socket)
                    self.manager.startThread(forward, client_socket, dock_socket)

            except socket.timeout:
                self.logDebug("Connection timed out, retrying...")
                return self._server(ip, webport, cnlport, thread)

            finally:
                server_socket.close()
                client_socket.close()
                dock_socket.close()

        except socket.error, e:
            self.logError(e)
            time.sleep(120)
            self._server(ip, webport, cnlport, thread)
