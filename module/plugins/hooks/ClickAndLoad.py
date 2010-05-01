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

import asyncore
import socket
import thread

from module.plugins.Hook import Hook

class ClickAndLoad(Hook):
    def __init__(self, core):
        Hook.__init__(self, core)
        props = {}
        props['name'] = "ClickAndLoad"
        props['version'] = "0.2"
        props['description'] = """Gives abillity to use jd's click and load. depends on webinterface"""
        props['author_name'] = ("RaNaN", "mkaay")
        props['author_mail'] = ("RaNaN@pyload.de", "mkaay@mkaay.de")
        self.props = props
    
    def coreReady(self):
    	self.port = int(self.core.config['webinterface']['port'])
        if self.core.config['webinterface']['activated']:
            try:
                thread.start_new_thread(proxy, ("127.0.0.1", self.port, 9666))
            except:
                self.logger.error("ClickAndLoad port already in use.")


def proxy(*settings):
    thread.start_new_thread(server, settings)
    lock = thread.allocate_lock()
    lock.acquire()
    lock.acquire()

def server(*settings):
    try:
        dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dock_socket.bind(("127.0.0.1", settings[2]))
        dock_socket.listen(5)
        while True:
            client_socket = dock_socket.accept()[0]
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((settings[0], settings[1]))
            thread.start_new_thread(forward, (client_socket, server_socket))
            thread.start_new_thread(forward, (server_socket, client_socket))
    except:
        pass
    finally:
        thread.start_new_thread(server, settings)

def forward(source, destination):
    string = ' '
    while string:
        string = source.recv(1024)
        if string:
            destination.sendall(string)
        else:
            #source.shutdown(socket.SHUT_RD)
            destination.shutdown(socket.SHUT_WR)
