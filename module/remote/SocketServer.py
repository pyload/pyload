#!/usr/bin/env python
# -'- coding: utf-8 -*.
"""
authored by:  RaNaN

This modul class handels all incoming and outgoing data between server and gui

"""
import asynchat
import asyncore
import socket
import threading


class ServerThread(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.server = MainServerSocket(7272, pycore)
        
    def run(self):
        asyncore.loop()
        print "loop closed"


class MainServerSocket(asyncore.dispatcher):
    def __init__(self, port, pycore):
        print 'initing MSS'
        asyncore.dispatcher.__init__(self)
        self.pycore = pycore
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('localhost', port))
        self.listen(5)
    def handle_accept(self):
        newSocket, address = self.accept()
        print "Connected from", address
        SecondaryServerSocket(newSocket, self.pycore)
    def handle_close(self):
	    print "going to close"
	    self.close()


class SecondaryServerSocket(asynchat.async_chat):
    def __init__(self, pycore, *args):
        print 'initing SSS'
        self.pycore = pycore
        asynchat.async_chat.__init__(self, *args)
        self.set_terminator('\n')
        self.data = []
    def collect_incoming_data(self, data):
        self.data.append(data)
    def found_terminator(self):
        self.push("daten")
        self.data = []
        #having fun with the data
    def handle_close(self):
        print "Disconnected from", self.getpeername()
        self.close()