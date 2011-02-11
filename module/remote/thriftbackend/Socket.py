# -*- coding: utf-8 -*-

import socket

from thrift.transport.TSocket import TSocket, TServerSocket, TTransportException


class Socket(TSocket):
    def __init__(self, host='localhost', port=7228, ssl=False):
        TSocket.__init__(self, host, port)
        self.ssl = ssl

    def open(self):
        self.handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.handle.settimeout(self._timeout)
        self.handle.connect((self.host, self.port))


class ServerSocket(TServerSocket, Socket):
    def __init__(self, port=7228, host="0.0.0.0", key="", cert=""):
        self.host = host
        self.port = port
        self.handle = None

    def listen(self):
        self.handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(self.handle, 'set_timeout'):
          self.handle.set_timeout(None)
        self.handle.bind((self.host, self.port))
        self.handle.listen(128)