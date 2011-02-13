# -*- coding: utf-8 -*-

from thrift.transport.TTransport import TBufferedTransport

class Transport(TBufferedTransport):
    DEFAULT_BUFFER = 4096

    def __init__(self, trans, rbuf_size = DEFAULT_BUFFER):
        TBufferedTransport.__init__(self, trans, rbuf_size)
        self.remoteaddr = trans.handle.getpeername()

class TransportFactory:
    def getTransport(self, trans):
        buffered = Transport(trans)
        return buffered
