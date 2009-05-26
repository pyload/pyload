#!/usr/bin/env python
# -'- coding: utf-8 -*.
"""
authored by:  RaNaN

This modul class handels all incoming and outgoing data between server and gui

"""
import threading
import socket
import asyncore
import asynchat

class ServerThread(threading.Thread):
	
	def __init__(self):
		threading.Thread.__init__ (self)
		self.server = MainServerSocket(7272)

	def run(self):
		asyncore.loop()
		
	def stop(self):
		asyncore.socket_map.clear()
		self.server.close()


class MainServerSocket(asyncore.dispatcher):
    def __init__(self, port):
        print 'initing MSS'
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('',port))
        self.listen(5)
    def handle_accept(self):
        newSocket, address = self.accept()
        print "Connected from", address
        SecondaryServerSocket(newSocket)
    def handle_close(self):
	    print "going to close"
	    self.close()



class SecondaryServerSocket(asynchat.async_chat):
    def __init__(self, *args):
        print 'initing SSS'
        asynchat.async_chat.__init__(self, *args)
        self.set_terminator('\n')
        self.data = []
    def collect_incoming_data(self, data):
        self.data.append(data)
    def found_terminator(self):
        self.push(''.join(self.data))
        self.data = []
        #having fun with the data
    def handle_close(self):
        print "Disconnected from", self.getpeername()
        self.close()