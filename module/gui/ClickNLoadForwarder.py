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
"""

from PyQt4.QtCore import QObject, SIGNAL

import logging, socket, errno, thread

class ClickNLoadForwarder(QObject):
    """
        Port forwarder to a remote Core's ClickNLoad plugin
    """

    def __init__(self):
        QObject.__init__(self)
        self.log = logging.getLogger("guilog")
        self.doStop  = False
        self.running = False
        self.error   = False
        self.connect(self, SIGNAL("messageBox_19"), self.messageBox_19)
        self.connect(self, SIGNAL("messageBox_20"), self.messageBox_20)

    def start(self, localIp, localPort, extIp, extPort):
        if self.running:
            raise RuntimeError("Port forwarder already started")
        self.localIp   = str(localIp)
        self.localPort = int(localPort)
        self.extIp     = str(extIp)
        self.extPort   = int(extPort)
        self.log.info("ClickNLoadForwarder: Starting port forwarding from %s:%d to %s:%d" % (self.localIp, self.localPort, self.extIp, self.extPort))
        self.doStop = False
        self.error  = False
        thread.start_new_thread(self.server, ())

    def stop(self):
        if not self.running:
            return
        self.doStop = True
        # wait max 10sec
        for dummy in range(0, 100):
            if not self.running:
                break
            sleep(0.1)
        if self.running:
            self.log.error("ClickNLoadForwarder.stop: Failed to stop port forwarding.")
            self.emit(SIGNAL("messageBox_19"))
        else:
            self.log.info("ClickNLoadForwarder: Port forwarder stopped.")

    def server(self):
        self.running = True
        self.forwardError = False
        try:
            self.dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.dock_socket.settimeout(0.2)
            self.dock_socket.bind((self.localIp, self.localPort))
            self.dock_socket.listen(5)
        except socket.error, x:
            if x.args[0] == errno.EADDRINUSE:
                self.log.error("ClickNLoadForwarder.server: Cannot bind to port %d, the port is occupied." % self.localPort)
                self.log.info("ClickNLoadForwarder.server: If you are pretty sure that the port should be free, try waiting 2-3 minutes for the operating system to close the port.")
            self.onRaise()
            raise
        except Exception:
            self.onRaise()
            raise
        while True:
            if self.doStop:
                self.log.debug9("ClickNLoadForwarder.server: stopped (1)")
                self.exitOnStop()
            if self.forwardError:
                self.exitOnForwardError()
            try:
                self.client_socket = self.dock_socket.accept()[0] # blocking call
            except socket.timeout:
                continue
            except socket.error:
                if self.doStop:
                    self.log.debug9("ClickNLoadForwarder.server: stopped (2)")
                    self.exitOnStop()
                elif self.forwardError:
                    self.exitOnForwardError()
                else:
                    self.onRaise()
                    raise
            except Exception:
                self.onRaise()
                raise
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.extIp, self.extPort))
                thread.start_new_thread(self.forward, (self.client_socket, self.server_socket))
                thread.start_new_thread(self.forward, (self.server_socket, self.client_socket))
            except Exception:
                if self.doStop:
                    self.log.debug9("ClickNLoadForwarder.server: stopped (3)")
                    self.exitOnStop()
                elif self.forwardError:
                    self.exitOnForwardError()
                else:
                    self.onRaise()
                    raise

    def forward(self, source, destination):
        string = " "
        while string:
            if self.doStop or self.error or self.forwardError or not self.running:
                self.log.debug9("ClickNLoadForwarder.forward: thread aborted")
                thread.exit()
            try:
                string = source.recv(1024) # throws EWOULDBLOCK when there is no data to read yet
                if string:
                    destination.sendall(string)
                else:
                    #source.shutdown(socket.SHUT_RD)
                    destination.shutdown(socket.SHUT_WR)
            except socket.error, x:
                if x.args[0] == errno.EWOULDBLOCK:
                    sleep(0.2)
                    continue
                elif not self.forwardError:
                    self.forwardError = True
                    self.log.error("ClickNLoadForwarder.forward: Unexpected socket error")
            except Exception:
                if not self.forwardError:
                    self.forwardError = True
                    self.log.error("ClickNLoadForwarder.forward: Unexpected error")

    def exitOnStop(self):
        self.closeSockets()
        self.error = False
        self.running = False
        thread.exit()

    def exitOnForwardError(self):
        self.closeSockets()
        self.error = True
        self.running = False
        self.log.error("ClickNLoadForwarder.exitOnForwardError: Port forwarding stopped.")
        self.emit(SIGNAL("messageBox_20"))
        thread.exit()

    def onRaise(self):
        self.closeSockets()
        self.error = True
        self.running = False
        self.log.error("ClickNLoadForwarder.onRaise: Port forwarding stopped.")
        self.emit(SIGNAL("messageBox_20"))

    def closeSockets(self):
        try:    self.server_socket.shutdown(socket.SHUT_RD)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (1) when shutting down the read side of the socket")
        try:    self.server_socket.shutdown(socket.SHUT_WR)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (1) when shutting down the write side of the socket")
        try:    self.server_socket.close()
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (1) when closing the socket")
        try:    self.client_socket.shutdown(socket.SHUT_RD)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (2) when shutting down the read side of the socket")
        try:    self.client_socket.shutdown(socket.SHUT_WR)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (2) when shutting down the write side of the socket")
        try:    self.client_socket.close()
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (2) when closing the socket")
        try:    self.dock_socket.shutdown(socket.SHUT_RD)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (3) when shutting down the read side of the socket")
        try:    self.dock_socket.shutdown(socket.SHUT_WR)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (3) when shutting down the write side of the socket")
        try:    self.dock_socket.close()
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (3) when closing the socket")

    def messageBox_19(self):
        self.emit(SIGNAL("msgBoxError"), _("Failed to stop ClickNLoad port forwarding."))

    def messageBox_20(self):
        self.emit(SIGNAL("msgBoxError"), _("ClickNLoad port forwarding stopped due to an error."))

