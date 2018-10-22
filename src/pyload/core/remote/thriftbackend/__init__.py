# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

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
                self.pyload.log.info(self._("Using SSL ThriftBackend"))
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
