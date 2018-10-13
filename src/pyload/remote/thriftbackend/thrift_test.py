# -*- coding: utf-8 -*-

import sys
import xmlrpc.client
from builtins import input, range
from getpass import getpass
import os
from time import time

from pyload.remote.thriftbackend.protocol import Protocol
from pyload.remote.thriftbackend.socket import Socket
from pyload.remote.thriftbackend.thriftgen import Pyload
from pyload.remote.thriftbackend.thriftgen.ttypes import *
from thrift import Thrift
from thrift.transport import TTransport

path = os.path.join((os.path.abspath(os.path.dirname(__file__))), "..", "..", "lib")
sys.path.append(path)


def bench(f, *args, **kwargs):
    s = time()
    ret = [f(*args, **kwargs) for i in range(0, 100)]
    e = time()
    try:
        print("{}: {} s".format(f._Method__name, e - s))
    except BaseException:
        print("{}: {} s".format(f.__name__, e - s))
    return ret


user = input("user ")
passwd = getpass("password ")

server_url = "http{}://{}:{}@{}:{}/".format("", user, passwd, "127.0.0.1", 7227)
proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True)

bench(proxy.get_server_version)
bench(proxy.status_server)
bench(proxy.status_downloads)
# bench(proxy.get_queue)
# bench(proxy.get_collector)
print()
try:

    # Make socket
    transport = Socket("localhost", 7228, False)

    # Buffering is critical. Raw sockets are very slow
    transport = TTransport.TBufferedTransport(transport)

    # Wrap in a protocol
    protocol = Protocol(transport)

    # Create a client to use the protocol encoder
    client = Pyload.Client(protocol)

    # Connect!
    transport.open()

    print("Login", client.login(user, passwd))

    bench(client.getServerVersion)
    bench(client.statusServer)
    bench(client.statusDownloads)
    # bench(client.getQueue)
    # bench(client.getCollector)

    print()
    print(client.getServerVersion())
    print(client.statusServer())
    print(client.statusDownloads())
    q = client.getQueue()

    for p in q:
        data = client.getPackageData(p.pid)
        print(data)
        print("Package Name: ", data.name)

    # Close!
    transport.close()

except Thrift.TException as tx:
    print("ThriftExpection: {}".format(tx.message))
