#!/usr/bin/env python
# -'- coding: utf-8 -*.
"""
authored by:  Captain Blackbeard

script only for socket testing

"""

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 7272))
print "Connected to server"
data = """A few lines of data to test the operation of both server and client.
Und noch eine Zeile"""
for line in data.splitlines():
    sock.sendall(line+'\n')
    print "Sent:", line

response = sock.recv(8192)

print "Received:", response 
sock.close()
