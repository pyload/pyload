#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
authored by:  RaNaN

this module handels the incoming requests

"""
import hashlib
import wx

from Crypto.Cipher import Blowfish
from RequestHandler import RequestHandler

class ClientHandler(RequestHandler):
    def __init__(self, client, pw):
        self.client = client
        key = hashlib.sha256(pw)
        self.bf = Blowfish.new(key.hexdigest(), Blowfish.MODE_ECB)

    def proceed(self, data):
        obj = self.decrypt(data)
	if obj.function == "get_downloads":
	    self.client.show_links(obj.response)
        return self.encrypt(obj)
