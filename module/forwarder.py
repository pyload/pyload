# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""

from sys import argv
from sys import exit

import socket
import thread

from traceback import print_exc

class Forwarder():

    def __init__(self, extip,extport=9666):
        print "Start portforwarding to %s:%s" % (extip, extport)
        proxy(extip, extport, 9666)


def proxy(*settings):
    while True:
        server(*settings)

def server(*settings):
    try:
        dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dock_socket.bind(("127.0.0.1", settings[2]))
        dock_socket.listen(5)
        while True:
            client_socket = dock_socket.accept()[0]
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((settings[0], settings[1]))
            thread.start_new_thread(forward, (client_socket, server_socket))
            thread.start_new_thread(forward, (server_socket, client_socket))
    except Exception:
        print_exc()
        
        
def forward(source, destination):
    string = ' '
    while string:
        string = source.recv(1024)
        if string:
            destination.sendall(string)
        else:
            #source.shutdown(socket.SHUT_RD)
            destination.shutdown(socket.SHUT_WR)

if __name__ == "__main__":
    args = argv[1:]
    if not args:
        print "Usage: forwarder.py <remote ip> <remote port>"
        exit()
    if len(args) == 1:
        args.append(9666)
        
    f = Forwarder(args[0], int(args[1]))
            