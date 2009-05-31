#!/usr/bin/env python
# -'- coding: utf-8 -*.
"""
authored by:  RaNaN

socket for connecting to the core's server

"""
import asynchat
import socket

from ClientHandler import ClientHandler

class ClientSocket(asynchat.async_chat):    
    def __init__(self, client):
        asynchat.async_chat.__init__(self)
        self.client = client
        self.data = ""
        self.handler = ClientHandler(None)
        self.set_terminator("\n")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def handle_connect(self):
        print "connected"

    def handle_close(self):
        print "Disconnected from", self.getpeername()
        self.close()

    def collect_incoming_data(self, data):
        print "data arrived"
        self.data += data

    def found_terminator(self):
        obj = self.handler.proceed(data)
        self.push(obj)
        print "pushed"
        data = ""
