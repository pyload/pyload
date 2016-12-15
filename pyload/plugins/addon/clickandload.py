# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
import socket
import _thread

from pyload.plugins.addon import Addon


class ClickAndLoad(Addon):
    __name__ = "ClickAndLoad"
    __version__ = "0.22"
    __description__ = """Gives abillity to use jd's click and load. depends on webinterface"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("extern", "bool", "Allow external link adding", False)]
    __author_name__ = ("RaNaN", "mkaay")
    __author_mail__ = ("RaNaN@pyload.de", "mkaay@mkaay.de")

    def coreReady(self):
        self.port = int(self.config['webui']['port'])
        if self.getConfig("extern"):
            ip = "0.0.0.0"
        else:
            ip = "127.0.0.1"

        _thread.start_new_thread(proxy, (self, ip, self.port, 9666))


def proxy(self, *settings):
    _thread.start_new_thread(server, (self,) + settings)
    lock = _thread.allocate_lock()
    lock.acquire()
    lock.acquire()


def server(self, *settings):
    try:
        dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dock_socket.bind((settings[0], settings[2]))
        dock_socket.listen(5)
        while True:
            client_socket = dock_socket.accept()[0]
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect(("127.0.0.1", settings[1]))
            _thread.start_new_thread(forward, (client_socket, server_socket))
            _thread.start_new_thread(forward, (server_socket, client_socket))
    except socket.error as e:
        if hasattr(e, "errno"):
            errno = e.errno
        else:
            errno = e.args[0]

        if errno == 98:
            self.logWarning(_("Click'N'Load: Port 9666 already in use"))
            return
        _thread.start_new_thread(server, (self,) + settings)
    except Exception:
        _thread.start_new_thread(server, (self,) + settings)


def forward(source, destination):
    string = ' '
    while string:
        string = source.recv(1024)
        if string:
            destination.sendall(string)
        else:
            #source.shutdown(socket.SHUT_RD)
            destination.shutdown(socket.SHUT_WR)
