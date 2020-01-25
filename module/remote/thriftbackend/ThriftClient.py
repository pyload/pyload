# -*- coding: utf-8 -*-

import sys
from socket import error
from os.path import dirname, abspath, join
from traceback import print_exc

try:
    import thrift
except ImportError:
    sys.path.append(abspath(join(dirname(abspath(__file__)), "..", "..", "lib")))

from thrift.transport import TTransport
#from thrift.transport.TZlibTransport import TZlibTransport
from CoreSocket import Socket
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
    def __init__(self, host="localhost", port=7227, user="", password=""):

        self.ssl = False
        self.createConnection(host, port, self.ssl)
        try:
            self.transport.open()
        except error, e:
            if e.args and e.args[0] in (111, 10061):
                raise NoConnection
            else:
                print_exc()
                raise NoConnection

        errorException = eofException = False
        e = None
        try:
            correct = self.client.login(user, password)
        except error, e:
            errorException = True
        except TTransport.TTransportException, e:
            if e.type == TTransport.TTransportException.END_OF_FILE:
                eofException = True
            else:
                print_exc()
                raise NoConnection

        if ((errorException and e.args and e.args[0] == 104) or         # linux client, linux server
                eofException or                                         # mixed linux/windows client/server
                (errorException and e.args and e.args[0] == 10054)):    # windows client, windows server
            # probably wants ssl
            try:
                self.ssl = True
                self.createConnection(host, port, self.ssl)
                #set timeout or a ssl socket will block when querying none ssl server
                self.socket.setTimeout(10 *1000)   # milliseconds
            except ImportError:
                #@TODO untested
                raise NoSSL
            except:
                print_exc()
                raise NoConnection
            try:
                self.transport.open()
            except:
                raise NoConnection
            try:
                correct = self.client.login(user, password)
            except:
                raise NoSSL
            finally:
                self.socket.setTimeout(None)

        elif errorException and (e.args and e.args[0] == 32):
            raise NoConnection

        elif errorException:
            print_exc()
            raise NoConnection

        if not correct:
            self.transport.close()
            raise WrongLogin

    def isSSLConnection(self):
        return self.ssl

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