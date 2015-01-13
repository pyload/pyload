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


class ClickAndLoad(Hook):
    __name__    = "ClickAndLoad"
    __type__    = "hook"
    __version__ = "0.26"

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
                client_socket = socket.create_connection(("127.0.0.1", webport))

                hookManager.startThread(forward, server_socket, client_socket)
                hookManager.startThread(forward, client_socket, server_socket)

        except socket.error, e:
            self.logError(e)
            self.server(ip, webport, cnlport)

        finally:
            dock_socket.close()
