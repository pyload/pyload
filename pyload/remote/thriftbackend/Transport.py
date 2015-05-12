# -*- coding: utf-8 -*-

import thrift


class Transport(thrift.transport.TTransport.TBufferedTransport):
    DEFAULT_BUFFER = 4096


    def __init__(self, trans, rbuf_size = DEFAULT_BUFFER):
        thrift.transport.TTransport.TBufferedTransport.__init__(self, trans, rbuf_size)
        self.handle = trans.handle
        self.remoteaddr = trans.handle.getpeername()


class TransportCompressed(thrift.transport.TZlibTransport.TZlibTransport):
    DEFAULT_BUFFER = 4096


    def __init__(self, trans, rbuf_size = DEFAULT_BUFFER):
        thrift.transport.TZlibTransport.TZlibTransport.__init__(self, trans, rbuf_size)
        self.handle = trans.handle
        self.remoteaddr = trans.handle.getpeername()


class TransportFactory(object):

    def getTransport(self, trans):
        buffered = Transport(trans)
        return buffered


class TransportFactoryCompressed(object):
    _last_trans = None
    _last_z = None


    def getTransport(self, trans, compresslevel=9):
        if trans == self._last_trans:
          return self._last_z
        ztrans = TransportCompressed(Transport(trans), compresslevel)
        self._last_trans = trans
        self._last_z = ztrans
        return ztrans
