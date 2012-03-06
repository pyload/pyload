# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
    @interface-version: 0.2
"""

import socket
import thread

from module.plugins.Addon import Addon

class ClickAndLoad(Addon):
    __name__ = "ClickAndLoad"
    __version__ = "0.2"
    __description__ = """Gives abillity to use jd's click and load. depends on webinterface"""
    __config__ = [("activated", "bool", "Activated", "True"),
                  ("extern", "bool", "Allow external link adding", "False")]
    __author_name__ = ("RaNaN", "mkaay")
    __author_mail__ = ("RaNaN@pyload.de", "mkaay@mkaay.de")

    def activate(self):
        self.port = int(self.core.config['webinterface']['port'])
        if self.core.config['webinterface']['activated']:
            try:
                if self.getConfig("extern"):
                    ip = "0.0.0.0"
                else:
                    ip = "127.0.0.1"

                thread.start_new_thread(proxy, (self, ip, self.port, 9666))
            except:
                self.log.error("ClickAndLoad port already in use.")


def proxy(self, *settings):
    thread.start_new_thread(server, (self,) + settings)
    lock = thread.allocate_lock()
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
            thread.start_new_thread(forward, (client_socket, server_socket))
            thread.start_new_thread(forward, (server_socket, client_socket))
    except socket.error, e:
        if hasattr(e, "errno"):
            errno = e.errno
        else:
            errno = e.args[0]

        if errno == 98:
            self.core.log.warning(_("Click'N'Load: Port 9666 already in use"))
            return
        thread.start_new_thread(server, (self,) + settings)
    except:
        thread.start_new_thread(server, (self,) + settings)


def forward(source, destination):
    string = ' '
    while string:
        string = source.recv(1024)
        if string:
            destination.sendall(string)
        else:
            #source.shutdown(socket.SHUT_RD)
            destination.shutdown(socket.SHUT_WR)
