# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import socketserver

from pyload.core.remote.remote_manager import BackendBase


class RequestHandler(socketserver.BaseRequestHandler):
    def setup(self):
        pass

    def handle(self):

        print(self.request.recv(1 << 10))


class SocketBackend(BackendBase):
    def setup(self, host, port):
        # local only
        self.server = socketserver.ThreadingTCPServer(
            ("localhost", port), RequestHandler
        )

    def serve(self):
        self.server.serve_forever()
