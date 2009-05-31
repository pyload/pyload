#!/usr/bin/env python
# -'- coding: utf-8 -*.
"""
authored by:  RaNaN

script only for socket testing

"""
import base64
import hashlib
import random
import string

import cPickle
from Crypto.Cipher import Blowfish
from module.remote.RequestObject import RequestObject
from module.remote.ClientSocket import ClientSocket

class Handler:
    def __init__(self):
        key = hashlib.sha256("pwhere")
        print key.hexdigest()
        self.bf = Blowfish.new(key.hexdigest(), Blowfish.MODE_ECB)

    def proceed(self, data):

        return self.decrypt(self.encrypt(str(("lol", "mehrlol", "pff"))))

    def decrypt(self, dec_str):
        try:
            dec_str = base64.standard_b64decode(dec_str)
            dec_str = self.bf.decrypt(dec_str)

            dec_str = dec_str[:-(int(dec_str[-1], 16) + 1)]
            obj = cPickle.loads(dec_str)
        except:
            obj = None
        return obj

    def encrypt(self, obj):
        enc_str = cPickle.dumps(obj, 1)
        padding = len(enc_str) % 16
        padding = 16 - padding

        p_str = ""
        for i in range(padding - 1):
            p_str += random.choice(string.letters + string.digits)
        p_str += hex(len(p_str)).replace("0x", "")
        enc_str += p_str

        enc_str = self.bf.encrypt(enc_str)
        enc_str = base64.standard_b64encode(enc_str)
        return enc_str



import socket

handler = Handler()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 7272))
print "Connected to server"

obj = RequestObject()
obj.command = "exec"
obj.function = "get_downloads"

sock.sendall(handler.encrypt(obj) + "\n")

response = sock.recv(8192)

print "Received:", handler.decrypt(response).response
sock.close()
