#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
authored by:  RaNaN

This modul class handels all incoming and outgoing data between server and gui

"""
import asynchat
import asyncore
import socket
import threading

from RequestHandler import RequestHandler


class ServerThread(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.server = MainServerSocket(int(pycore.config['port']), pycore)

    def run(self):
        asyncore.loop()
        print "loop closed"

    def sockets(self):
        """returns all connected sockets in a list"""
        sockets = []
        for value in asyncore.socket_map.values():
            if SecondaryServerSocket == value.__class__:
                sockets.append(value)

        return sockets

    def push_all(self, obj):
        """push obj to all sockets"""
        for socket in self.sockets():
            socket.push_obj(obj)


class MainServerSocket(asyncore.dispatcher):
    def __init__(self, port, pycore):
        asyncore.dispatcher.__init__(self)
        pycore.logger.info('initing Remote-Server')
        self.pycore = pycore
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('localhost', port))
        self.listen(5)
    def handle_accept(self):
        newSocket, address = self.accept()
        self.pycore.logger.info("Connected from " + str(address))
        SecondaryServerSocket(newSocket, self.pycore)
    def handle_close(self):
        print "going to close"
        self.close()


class SecondaryServerSocket(asynchat.async_chat):
    def __init__(self, socket, pycore):
        asynchat.async_chat.__init__(self, socket)
        self.pycore = pycore
        self.handler = RequestHandler(pycore)
        self.set_terminator('\n')
        self.data = ""
    def collect_incoming_data(self, data):
        self.data += data
    def found_terminator(self):
        rep = self.handler.proceed(self.data)
        self.push(rep)
        self.data = ""
        #having fun with the data
    def handle_close(self):
        self.pycore.logger.info("Disconnected from "+ str(self.getpeername()))
        self.close()
    def push_obj(self, obj):
        obj = self.handler.encrypt(obj)
        self.push(obj)
