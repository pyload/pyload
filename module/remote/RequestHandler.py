#!/usr/bin/python
# -*- coding: utf-8 -*- 
"""
authored by:  RaNaN

this module handels the incoming requests

"""

import base64
import random
import string

import cPickle
from Crypto.Cipher import AES
from Crypto.Hash import MD5
from Crypto.Hash import SHA
from RequestObject import RequestObject


class RequestHandler:
    def __init__(self, core):
        self.core = core
        key = SHA.new(core.config['remotepassword'])
        key = MD5.new(key.hexdigest())
        self.aes = AES.new(key.hexdigest(), AES.MODE_ECB)

    def proceed(self, data):
        obj = self.decrypt(data)

        if obj.command == "exec":
            func = getattr(self.core, obj.function)
            obj.response = func()
        else:
            obj.response = "antwort"
        
        return self.encrypt(obj)


    def decrypt(self, dec_str):
        dec_str = base64.standard_b64decode(dec_str)
        dec_str = self.aes.decrypt(dec_str)
        
        dec_str = dec_str[:-(int(dec_str[-1], 16) + 1)]
        obj = cPickle.loads(dec_str)
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

        enc_str = self.aes.encrypt(enc_str)
        enc_str = base64.standard_b64encode(enc_str)
        return enc_str



