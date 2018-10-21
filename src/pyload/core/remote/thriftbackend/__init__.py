# -*- coding: utf-8 -*-
# @author: mkaay, RaNaN

import os
from builtins import _

from thrift.server import TServer

from pyload.core.remote.remote_manager import BackendBase
from pyload.core.remote.thriftbackend.processor import Processor
from pyload.core.remote.thriftbackend.protocol import ProtocolFactory
from pyload.core.remote.thriftbackend.socket import ServerSocket
from pyload.core.remote.thriftbackend.transport import TransportFactory

# from pyload.core.remote.thriftbackend.transport import TransportFactoryCompressed


class ThriftBackend(BackendBase):
    def setup(self, host, port):
        processor = Processor(self.pyload.api)

        key = None
        cert = None

        if self.pyload.config.get("ssl", "activated"):
            if os.path.exists(self.pyload.config.get("ssl", "cert")) and os.path.exists(
                self.pyload.config.get("ssl", "key")
            ):
                self.pyload.log.info(_("Using SSL ThriftBackend"))
                key = self.pyload.config.get("ssl", "key")
                cert = self.pyload.config.get("ssl", "cert")

        transport = ServerSocket(port, host, key, cert)

        #        tfactory = TransportFactoryCompressed()
        tfactory = TransportFactory()
        pfactory = ProtocolFactory()

        self.server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
        # self.server = TNonblockingServer.TNonblockingServer(processor, transport, tfactory, pfactory)

        # server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)

    def serve(self):
        self.server.serve()
