#!/usr/bin/python
# -*- coding: utf-8 -*- 
"""
authored by:  RaNaN

this module handels the incoming requests

"""

import base64
import hashlib
import random
import string

import cPickle
from Crypto.Cipher import Blowfish
from RequestObject import RequestObject


class RequestHandler:
    def __init__(self, core):
        self.core = core
        key = hashlib.sha256("pwhere") #core.config['remotepassword']
        self.bf = Blowfish.new(key.hexdigest(), Blowfish.MODE_ECB)

    def proceed(self, data):
        obj = self.decrypt(data)

        if obj.command == "exec":
            func = getattr(self.core, obj.function)
            obj.response = func( * obj.args)
        else:
            obj.response = "error happend"
        
        return self.encrypt(obj)


    def decrypt(self, dec_str):
        try:
            dec_str = base64.standard_b64decode(dec_str)
            dec_str = self.bf.decrypt(dec_str)
        
            dec_str = dec_str[:-(int(dec_str[-1], 16) + 1)]
            obj = cPickle.loads(dec_str)
        except:
            obj = RequestObject()

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



