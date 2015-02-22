# -*- coding: utf-8 -*-

import socket
import time

from threading import Lock

from pyload.plugin.Addon import Addon, threaded


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
class ClickAndLoad(Addon):
    __name    = "ClickAndLoad"
    __type    = "addon"
    __version = "0.37"

    __config = [("activated", "bool", "Activated"                             , True),
                ("port"     , "int" , "Port"                                  , 9666),
                ("extern"   , "bool", "Listen on the public network interface", True)]

    __description = """Click'N'Load addon plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def activate(self):
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
