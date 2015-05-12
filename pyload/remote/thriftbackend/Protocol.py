# -*- coding: utf-8 -*-

import thrift


class Protocol(thrift.protocol.TBinaryProtocol.thrift.protocol.TBinaryProtocol):

    def writeString(self, str):
        try:
            str = str.encode("utf8", "ignore")
        except Exception:
            pass

        self.writeI32(len(str))
        self.trans.write(str)


    def readString(self):
        len = self.readI32()
        str = self.trans.readAll(len)
        try:
            str = str.decode("utf8", "ignore")
        except Exception:
            pass

        return str


class ProtocolFactory(thrift.protocol.TBinaryProtocol.thrift.protocol.TBinaryProtocolFactory):

    def getProtocol(self, trans):
        prot = Protocol(trans, self.strictRead, self.strictWrite)
        return prot
