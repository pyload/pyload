#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from sys import argv, exit

import _thread


class Forwarder:
    def __init__(self, extip, extport=9666):
        print(f"Start portforwarding to {extip}:{extport}")
        proxy(extip, extport, 9666)


def proxy(*settings):
    while True:
        server(*settings)


def server(*settings):
    dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dock_socket.bind(("127.0.0.1", settings[2]))
    dock_socket.listen(5)
    while True:
        client_socket = dock_socket.accept()[0]
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((settings[0], settings[1]))
        _thread.start_new_thread(forward, (client_socket, server_socket))
        _thread.start_new_thread(forward, (server_socket, client_socket))


def forward(source, destination):
    string = " "
    while string:
        string = source.recv(1 << 10)
        if string:
            destination.sendall(string)
        else:
            # source.shutdown(socket.SHUT_RD)
            destination.shutdown(socket.SHUT_WR)


if __name__ == "__main__":
    args = argv[1:]
    if not args:
        print("Usage: forwarder.py <remote ip> <remote port>")
        exit()
    if len(args) == 1:
        args.append(9666)

    f = Forwarder(args[0], int(args[1]))
