#!/usr/bin/env python
# -'- coding: utf-8 -*.
"""
authored by:  RaNaN

socket for connecting to the core's server

"""
import asynchat
import socket
from RequestHandler import RequestHandler

class ClientSocket(asynchat.async_chat):    
    def __init__(self, client):
	asynchat.async_chat.__init__(self)
	self.client = client
        self.data = ""
	self.handler = RequestHandler(None)
	self.set_terminator("\n")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def handle_connect(self):
	print "connected"
    
    def collect_incoming_data(self, data):
        self.data += data

    def found_terminator(self):
        pass
	#process
