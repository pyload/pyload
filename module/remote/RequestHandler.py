#!/usr/bin/python
# -*- coding: utf-8 -*- 
"""
authored by:  RaNaN

this module handels the incoming requests

"""

import base64
from cPickle import Pickler
from cStringIO import StringIO
from Crypto.Cipher import AES


class RequestHandler():
    def __init__(self, core):
	self.core = core
	self.p = Pickler(string)
	self.obj = AES.new('pw', AES.MODE_ECB)

    def proceed(self, data):
	return "the answer."

    def decrypt(self, string):
	string = string
	buf = StringIO(string)


