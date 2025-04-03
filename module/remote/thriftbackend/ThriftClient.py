# -*- coding: utf-8 -*-

import sys
from socket import error, timeout
from os.path import dirname, abspath, join
from traceback import print_exc

try:
    import thrift
except ImportError:
    sys.path.append(abspath(join(dirname(abspath(__file__)), "..", "..", "lib")))

from thrift.transport import TTransport
#from thrift.transport.TZlibTransport import TZlibTransport
from Socket import Socket
from Protocol import Protocol

# modules should import ttypes from here, when want to avoid importing API

from thriftgen.pyload import Pyload
from thriftgen.pyload.ttypes import *

ConnectionClosed = TTransport.TTransportException

class WrongLogin(Exception):
    pass

class NoConnection(Exception):
    pass

class NoSSL(Exception):
    pass

class ThriftClient:
    def __init__(self, host="localhost", port=7227, user="", password="", ssl="auto"):

        login_timeout_auto = 100   # ms
        login_timeout = 25000      # ms

        if ssl == "auto":
            (correct, wants_ssl) = self.login(host, port, user, password, login_timeout_auto)
            if wants_ssl:
                correct = self.loginSSL(host, port, user, password, login_timeout_auto)
        elif ssl == "yes":
            correct = self.loginSSL(host, port, user, password, login_timeout)
        elif ssl == "no":
            (correct, wants_ssl) = self.login(host, port, user, password, login_timeout)
            if wants_ssl:
                raise NoConnection

        if not correct:
            self.transport.close()
            raise WrongLogin

    def login(self, host, port, user, password, login_timeout):
        self.createConnection(host, port)
        # set timeout or a non-ssl socket may block when querying ssl server
        self.socket.setTimeout(login_timeout)

        try:
            self.transport.open()
        except error, e:
            if e.args and e.args[0] in (111, 10061):  # connection refused
                raise NoConnection
            else:
                print_exc()
                raise NoConnection

        correct = None
        wants_ssl = False
        try:
            correct = self.client.login(user, password)
        except (error, timeout), e:
            if ((e.args and e.args[0] == 104) or              # connection reset by peer
                    (e.args and e.args[0] == "timed out")):   # timeout
                # probably wants ssl
                wants_ssl = True
                #print "wants_ssl (%s)" % ("timeout" if e.args and e.args[0] == "timed out" else "connection reset by peer")
            elif e.args and e.args[0] == 32:   # broken pipe
                raise NoConnection
            else:
                print_exc()
                raise NoConnection
        finally:
            self.socket.setTimeout(None)   # set blocking mode

        return (correct, wants_ssl)

    def loginSSL(self, host, port, user, password, login_timeout):
        try:
            self.createConnection(host, port, True)
            # set timeout or a ssl socket will block when querying non-ssl server
            self.socket.setTimeout(login_timeout)
        except ImportError:
            raise NoSSL

        try:
            self.transport.open()
        except error, e:
            if e.args and e.args[0] in (111, 10061):  # connection refused
                raise NoConnection
            else:
                print_exc()
                raise NoConnection

        try:
            correct = self.client.login(user, password)
        except (error, timeout), e:
            if ((e.args and e.args[0] == 104) or              # connection reset by peer
                    (e.args and e.args[0] == "timed out")):   # timeout
                raise NoConnection
            elif e.args and e.args[0] == 32:   # broken pipe
                raise NoConnection
            else:
                print_exc()
                raise NoConnection
        finally:
            self.socket.setTimeout(None)   # set blocking mode

        return correct

    def createConnection(self, host, port, ssl=False):
        self.socket = Socket(host, port, ssl)
        self.transport = TTransport.TBufferedTransport(self.socket)
#        self.transport = TZlibTransport(TTransport.TBufferedTransport(self.socket))

        protocol = Protocol(self.transport)
        self.client = Pyload.Client(protocol)

    def close(self):
        self.transport.close()

    def __getattr__(self, item):
        return getattr(self.client, item)

if __name__ == "__main__":

    client = ThriftClient(user="User", password="pwhere")

    print client.getServerVersion()
    print client.statusServer()
    print client.statusDownloads()
    q = client.getQueue()

#    for p in q:
#      data = client.getPackageData(p.pid)
#      print data
#      print "Package Name: ", data.name


    print client.getServices()
    print client.call(Pyload.ServiceCall("UpdateManager", "recheckForUpdates"))

    print client.getConfigValue("download", "limit_speed", "core")

    client.close()