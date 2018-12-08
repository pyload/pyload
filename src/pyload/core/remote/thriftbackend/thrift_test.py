# -*- coding: utf-8 -*-

import time
import xmlrpc.client
from builtins import input, range
from contextlib import closing
from getpass import getpass

from thrift import Thrift
from thrift.transport import TTransport

from .protocol import Protocol
from .socket import Socket
from .thriftgen import pyload as Pyload
from .thriftgen.ttypes import *


def bench(f, *args, **kwargs):
    s = time.time()
    ret = [f(*args, **kwargs) for i in range(0, 100)]
    e = time.time()
    try:
        print(f"{f._Method__name}: {e - s} s")
    except BaseException:
        print(f"{f.__name__}: {e - s} s")
    return ret


user = input("user ")
passwd = getpass("password ")

server_url = "http://{user}:{passwd}@127.0.0.1:7227/"
proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True)

bench(proxy.get_server_version)
bench(proxy.status_server)
bench(proxy.status_downloads)
# bench(proxy.get_queue)
# bench(proxy.get_collector)
print()
try:
    # Make socket
    with closing(Socket("localhost", 7228, False)) as transport:

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

except Thrift.TException as tx:
    print(f"ThriftExpection: {tx.message}")
