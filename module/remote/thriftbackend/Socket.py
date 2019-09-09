# -*- coding: utf-8 -*-

import sys
import socket
import errno

from time import sleep

from thrift.transport.TSocket import TSocket, TServerSocket, TTransportException

WantReadError = Exception #overwritten when ssl is used

class SecureSocketConnection:
    def __init__(self, connection):
        self.__dict__["connection"] = connection

    def __getattr__(self, name):
        return getattr(self.__dict__["connection"], name)

    def __setattr__(self, name, value):
        setattr(self.__dict__["connection"], name, value)

    def shutdown(self, how=1):
        self.__dict__["connection"].shutdown()

    def accept(self):
        connection, address = self.__dict__["connection"].accept()
        return SecureSocketConnection(connection), address
    
    def send(self, buff):
        try:
            return self.__dict__["connection"].send(buff)
        except WantReadError:
            sleep(0.1)
            return self.send(buff)
    
    def recv(self, buff):
        try:
            return self.__dict__["connection"].recv(buff)
        except WantReadError:
            sleep(0.1)
            return self.recv(buff)

class Socket(TSocket):
    def __init__(self, host='localhost', port=7228, ssl=False):
        TSocket.__init__(self, host, port)
        self.ssl = ssl

    def open(self):
        if self.ssl:
            SSL = __import__("OpenSSL", globals(), locals(), "SSL", -1).SSL
            WantReadError = SSL.WantReadError
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            c = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            c.set_connect_state()
            self.handle = SecureSocketConnection(c)
        else:
            self.handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #errno 104 connection reset

        self.handle.settimeout(self._timeout)
        self.handle.connect((self.host, self.port))

    def read(self, sz):
        try:
            buff = self.handle.recv(sz)
        except socket.error, e:
            if (e.args[0] == errno.ECONNRESET and
                (sys.platform == 'darwin' or sys.platform.startswith('freebsd'))):
                # freebsd and Mach don't follow POSIX semantic of recv
                # and fail with ECONNRESET if peer performed shutdown.
                # See corresponding comment and code in TSocket::read()
                # in lib/cpp/src/transport/TSocket.cpp.
                self.close()
                # Trigger the check to raise the END_OF_FILE exception below.
                buff = ''
            else:
                raise
        except Exception, e:
            # SSL connection was closed
            if e.args == (-1, 'Unexpected EOF'):
                buff = ''
            elif e.args == ([('SSL routines', 'SSL23_GET_CLIENT_HELLO', 'unknown protocol')],):
                #a socket not using ssl tried to connect
                buff = ''
            else:
                raise
            
        if not len(buff):
            raise TTransportException(type=TTransportException.END_OF_FILE, message='TSocket read 0 bytes')
        return buff


class ServerSocket(TServerSocket, Socket):
    def __init__(self, port=7228, host="0.0.0.0", key="", cert=""):
        self.host = host
        self.port = port
        self.key = key
        self.cert = cert
        self.handle = None

    def listen(self):
        if self.cert and self.key:
            SSL = __import__("OpenSSL", globals(), locals(), "SSL", -1).SSL
            WantReadError = SSL.WantReadError
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ctx.use_privatekey_file(self.key)
            ctx.use_certificate_file(self.cert)

            tmpConnection = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            tmpConnection.set_accept_state()
            self.handle = SecureSocketConnection(tmpConnection)

        else:
            self.handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


        self.handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(self.handle, 'set_timeout'):
            self.handle.set_timeout(None)
        self.handle.bind((self.host, self.port))
        self.handle.listen(128)

    def accept(self):
        client, addr = self.handle.accept()
        result = Socket()
        result.setHandle(client)
        return result
