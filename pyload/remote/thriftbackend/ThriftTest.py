# -*- coding: utf-8 -*-

import getpass
import os
import platform
import sys
import time
import xmlrpclib

import thrift

from pyload.remote.thriftbackend.Protocol import Protocol
from pyload.remote.thriftbackend.Socket import Socket
from pyload.remote.thriftbackend.thriftgen.pyload import Pyload
from pyload.remote.thriftbackend.thriftgen.pyload.ttypes import *


def bench(f, *args, **kwargs):
    s = time.time()
    ret = [f(*args, **kwargs) for _i in xrange(0, 100)]
    e = time.time()
    try:
        print "%s: %f s" % (f._Method__name, e-s)
    except Exception:
        print "%s: %f s" % (f.__name__, e-s)
    return ret

user = raw_input("user ")
passwd = getpass.getpass("password ")

server_url = "http%s://%s:%s@%s:%s/" % (
  "",
  user,
  passwd,
  "127.0.0.1",
  7227
)
proxy = xmlrpclib.ServerProxy(server_url, allow_none=True)

bench(proxy.get_server_version)
bench(proxy.status_server)
bench(proxy.status_downloads)
# bench(proxy.get_queue)
# bench(proxy.get_collector)
print
try:

    # Make socket
    transport = Socket('localhost', 7228, False)

    # Buffering is critical. Raw sockets are very slow
    transport = thrift.transport.TTransport.TBufferedTransport(transport)

    # Wrap in a protocol
    protocol = Protocol(transport)

    # Create a client to use the protocol encoder
    client = Pyload.Client(protocol)

    # Connect!
    transport.open()

    print "Login", client.login(user, passwd)

    bench(client.getServerVersion)
    bench(client.statusServer)
    bench(client.statusDownloads)
    # bench(client.getQueue)
    # bench(client.getCollector)

    print
    print client.getServerVersion()
    print client.statusServer()
    print client.statusDownloads()
    q = client.getQueue()

    for p in q:
      data = client.getPackageData(p.pid)
      print data
      print "Package Name: ", data.name

    # Close!
    transport.close()

except thrift.Thrift.TException, tx:
    print 'ThriftExpection: %s' % tx.message
