# -*- coding: utf-8 -*-

from socket import socket, error
from threading import Thread

from pyload.plugins.Addon import Addon


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
    __name    = "ClickAndLoad"
    __type    = "addon"
    __version = "0.23"

    __config = [("activated", "bool", "Activated"                 , True ),
                ("port"     , "int" , "Port"                      , 9666 ),
                ("extern"   , "bool", "Allow external link adding", False)]

    __description = """Click'N'Load hook plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.de"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def setup(self):
        self.interval = 300


    def activate(self):
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
