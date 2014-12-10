# -*- coding: utf-8 -*-

from socket import socket, error
from threading import Thread

from pyload.plugins.internal.Addon import Addon


def forward(source, destination):
    string = ' '
    while string:
        string = source.recv(1024)
        if string:
            destination.sendall(string)
        else:
            #source.shutdown(socket.SHUT_RD)
            destination.shutdown(socket.SHUT_WR)


class ClickAndLoad(Addon):
    __name__    = "ClickAndLoad"
    __type__    = "addon"
    __version__ = "0.23"

    __config__ = [("activated", "bool", "Activated"                 , True ),
                  ("port"     , "int" , "Port"                      , 9666 ),
                  ("extern"   , "bool", "Allow external link adding", False)]

    __description__ = """Click'N'Load hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.de"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def setup(self):
        self.interval = 300


    def coreReady(self):
        self.initPeriodical()


    def periodical(self):
        webip   = "0.0.0.0" if self.getConfig("extern") else "127.0.0.1"
        webport = self.config['webinterface']['port']
        cnlport = self.getConfig("port"))

        try:
            s = socket()
            s.bind((webip, cnlport))
            s.listen(5)

            client = s.accept()[0]
            server = socket()

            server.connect(("127.0.0.1", webport))

        except error, e:
            if hasattr(e, "errno"):
                errno = e.errno
            else:
                errno = e.args[0]

            if errno == 98:
                self.logWarning(_("Port %d already in use") % cnlport)
            else:
                self.logDebug(e)

        else:
            self.core.scheduler.removeJob(self.cb)
            t = Thread(target=forward, args=[client, server])
            t.setDaemon(True)
            t.start()
