# -*- coding: utf-8 -*-

from thrift.transport.TTransport import TBufferedTransport
from thrift.transport.TZlibTransport import TZlibTransport

class Transport(TBufferedTransport):
    DEFAULT_BUFFER = 4096

    def __init__(self, trans, rbuf_size = DEFAULT_BUFFER):
        TBufferedTransport.__init__(self, trans, rbuf_size)
        self.handle = trans.handle
        self.remoteaddr = trans.handle.getpeername()

class TransportCompressed(TZlibTransport):
    DEFAULT_BUFFER = 4096

    def __init__(self, trans, rbuf_size = DEFAULT_BUFFER):
        TZlibTransport.__init__(self, trans, rbuf_size)
        self.handle = trans.handle
        self.remoteaddr = trans.handle.getpeername()

class TransportFactory:
    def getTransport(self, trans):
        buffered = Transport(trans)
        return buffered

class TransportFactoryCompressed:
    _last_trans = None
    _last_z = None

    def getTransport(self, trans, compresslevel=9):
        if trans == self._last_trans:
          return self._last_z
        ztrans = TransportCompressed(Transport(trans), compresslevel)
        self._last_trans = trans
        self._last_z = ztrans
        return ztrans