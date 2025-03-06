# -*- coding: utf-8 -*-

from thrift.protocol import TBinaryProtocol


class Protocol(TBinaryProtocol.TBinaryProtocol):
    def writeString(self, str):
        try:
            str = str.encode("utf-8", "ignore")
        except Exception:
            pass

        self.writeI32(len(str))
        self.trans.write(str)

    def readString(self):
        len = self.readI32()
        str = self.trans.readAll(len)
        return str


class ProtocolFactory(TBinaryProtocol.TBinaryProtocolFactory):
    def getProtocol(self, trans):
        prot = Protocol(trans, self.strictRead, self.strictWrite)
        return prot
