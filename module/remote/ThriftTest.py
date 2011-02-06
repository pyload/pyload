#!/usr/bin/env python

from thriftgen.pyload import Pyload
from thriftgen.pyload.ttypes import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from time import sleep, time

import xmlrpclib

def bench(f, *args, **kwargs):
    s = time()
    ret = f(*args, **kwargs)
    e = time()
    print "time", e-s
    return ret

server_url = "http%s://%s:%s@%s:%s/" % (
  "",
  "user",
  "password",
  "127.0.0.1",
  7227
)
proxy = xmlrpclib.ServerProxy(server_url, allow_none=True)

bench(proxy.get_server_version)
bench(proxy.get_queue)
bench(proxy.get_collector)
print
try:

  # Make socket
  transport = TSocket.TSocket('localhost', 9090)

  # Buffering is critical. Raw sockets are very slow
  transport = TTransport.TBufferedTransport(transport)

  # Wrap in a protocol
  protocol = TBinaryProtocol.TBinaryProtocol(transport)

  # Create a client to use the protocol encoder
  client = Pyload.Client(protocol)

  # Connect!
  transport.open()
  
  client.login("user", "password")
  
  bench(client.getServerVersion)
  bench(client.getQueue)
  bench(client.getCollector)

  # Close!
  transport.close()
  
except Thrift.TException, tx:
  print '%s' % (tx.message)
