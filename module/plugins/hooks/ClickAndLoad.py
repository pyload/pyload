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
    @interface-version: 0.1
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
        props['version'] = "0.1"
        props['description'] = """Gives abillity to use jd's click and load. depends on webinterface"""
        props['author_name'] = ("RaNaN")
        props['author_mail'] = ("RaNaN@pyload.de")
        self.props = props

	self.port = int(self.core.config['webinterface']['port'])
        if self.core.config['webinterface']['activated']:
            try:
                forwarder('127.0.0.1', 9666, '127.0.0.1', self.port)
                thread.start_new_thread(asyncore.loop, ())
            except:
                self.core.logger.error("ClickAndLoad port already in use.")


class forwarder(asyncore.dispatcher):
    def __init__(self, ip, port, remoteip, remoteport, backlog=5):
        asyncore.dispatcher.__init__(self)
        self.remoteip = remoteip
        self.remoteport = remoteport
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((ip, port))
        self.listen(backlog)

    def handle_accept(self):
        conn, addr = self.accept()
        # print '--- Connect --- '
        sender(receiver(conn), self.remoteip, self.remoteport)

class receiver(asyncore.dispatcher):
    def __init__(self, conn):
        asyncore.dispatcher.__init__(self, conn)
        self.from_remote_buffer = ''
        self.to_remote_buffer = ''
        self.sender = None

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        # print '%04i -->'%len(read)
        self.from_remote_buffer += read

    def writable(self):
        return (len(self.to_remote_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.to_remote_buffer)
        # print '%04i <--'%sent
        self.to_remote_buffer = self.to_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        if self.sender:
            self.sender.close()

class sender(asyncore.dispatcher):
    def __init__(self, receiver, remoteaddr, remoteport):
        asyncore.dispatcher.__init__(self)
        self.receiver = receiver
        receiver.sender = self
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((remoteaddr, remoteport))

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        # print '<-- %04i'%len(read)
        self.receiver.to_remote_buffer += read

    def writable(self):
        return (len(self.receiver.from_remote_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.receiver.from_remote_buffer)
        # print '--> %04i'%sent
        self.receiver.from_remote_buffer = self.receiver.from_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        self.receiver.close()
