# -*- coding: utf-8 -*-


from future import standard_library
standard_library.install_aliases()
import socketserver

from .RemoteManager import BackendBase

class RequestHandler(socketserver.BaseRequestHandler):

    def setup(self):
        pass

    def handle(self):

        print(self.request.recv(1024))



class SocketBackend(BackendBase):

    def setup(self, host, port):
        #local only
        self.server = socketserver.ThreadingTCPServer(("localhost", port), RequestHandler)

    def serve(self):
        self.server.serve_forever()
