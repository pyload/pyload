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

from .remote.remote_manager import BackendBase
from .processor import Processor
from .protocol import ProtocolFactory
from .socket import ServerSocket
from .transport import TransportFactory

# from .transport import TransportFactoryCompressed


class ThriftBackend(BackendBase):
    def setup(self, host, port):
        processor = Processor(self.pyload.api)

        key = None
        cert = None

        if self.pyload.config.get("ssl", "enabled"):
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
