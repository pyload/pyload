#!/usr/bin/env python
# -'- coding: utf-8 -*.
"""
authored by:  RaNaN

socket for connecting to the core's server

"""
import asynchat
import socket
import asyncore
import threading
import time

from ClientHandler import ClientHandler

class SocketThread(threading.Thread):
    def __init__(self, adress, port, pw, client):
	threading.Thread.__init__(self)
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((adress, port))
	self.socket = ClientSocket(sock, pw, client)
	self.start()
    def run(self):
	asyncore.loop()
	print "loop closed"


class ClientSocket(asynchat.async_chat):    
    def __init__(self, sock, pw, client):
        asynchat.async_chat.__init__(self, conn=sock)
        self.data = ""
        self.handler = ClientHandler(client, pw)
        self.set_terminator("\n")
        #self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

    def handle_close(self):
        print "Disconnected from", self.getpeername()
        self.close()

    def collect_incoming_data(self, data):
        self.data += data

    def found_terminator(self):
        obj = self.handler.proceed(self.data)
        #self.push(obj+"\n")
        print "data arrived"
        self.data = ""
