# -*- coding: utf-8 -*-
try:
    import SocketServer
    from RemoteManager import BackendBase
except ImportError:
    import socketserver as SocketServer
    from .RemoteManager import BackendBase


class RequestHandler(SocketServer.BaseRequestHandler):

    def setup(self):
        pass

    def handle(self):

        print (self.request.recv(1024))



class SocketBackend(BackendBase):

    def setup(self, host, port):
        #local only
        self.server = SocketServer.ThreadingTCPServer(("localhost", port), RequestHandler)

    def serve(self):
        self.server.serve_forever()
