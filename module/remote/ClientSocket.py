#!/usr/bin/env python
# -'- coding: utf-8 -*.
"""
authored by:  RaNaN

socket for connecting to the core's server

"""
import asynchat
import asyncore
import socket
import threading

from ClientHandler import ClientHandler
from RequestObject import RequestObject

class SocketThread(threading.Thread):
    def __init__(self, adress, port, pw, client):
	threading.Thread.__init__(self)
	self.setDaemon(True)
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((adress, port))
	self.socket = ClientSocket(sock, pw, client)
	self.start()

    def run(self):
	asyncore.loop()
	print "loop closed"

    def push_exec(self, function, args=[]):
	obj = RequestObject()
	obj.command = "exec"
	obj.function = function
	obj.args = args
	self.push(obj)

    def push(self, obj):
	self.socket.push_obj(obj)


class ClientSocket(asynchat.async_chat):    
    def __init__(self, sock, pw, client):
        asynchat.async_chat.__init__(self, sock)
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
        self.handler.proceed(self.data)
        self.data = ""

    def push_obj(self, obj):
	string = self.handler.encrypt(obj)
	self.push(string)

