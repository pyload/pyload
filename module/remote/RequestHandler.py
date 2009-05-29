#!/usr/bin/python
# -*- coding: utf-8 -*- 
"""
authored by:  RaNaN

this module handels the incoming requests

"""

import base64
import cPickle
import random
import string
from Crypto.Cipher import AES
from Crypto.Hash import SHA


class RequestHandler():
    def __init__(self, core):
	self.core = core
	key = SHA.new(core.config['remotepassword'])
	self.aes = AES.new(key.hexdigest()[:32], AES.MODE_ECB)

    def proceed(self, data):
	return self.encrypt({'befehl' : None , 'args':[1,2,3], 'test': 'lol'})

    def decrypt(self, dec_str):
	dec_str = base64.standard_b64decode(dec_str)
	dec_str = self.aes.decrypt(dec_str)

	dec_str = dec_str[:-(int(dec_str[-1],16)+1)]
	obj = cPickle.loads(dec_str)
	return obj

    def encrypt(self, obj):
	enc_str = cPickle.dumps(obj, 1)
	padding = len(enc_str) % 16
	padding = 16 - padding
	
	p_str = ""
	for i in range(padding - 1):
		p_str += random.choice(string.letters+string.digits)
	p_str += hex(len(p_str)).replace("0x","")
	enc_str += p_str

	enc_str = self.aes.encrypt(enc_str)
	enc_str = base64.standard_b64encode(enc_str)
	return enc_str



