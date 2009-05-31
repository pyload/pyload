#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
authored by:  RaNaN

this module handels the incoming requests

"""
import hashlib

from Crypto.Cipher import Blowfish
from RequestHandler import RequestHandler

class ClientHandler(RequestHandler):
    def __init__(self, client):
        self.client = client
        key = hashlib.sha256("pwhere")
        self.bf = Blowfish.new(key.hexdigest(), Blowfish.MODE_ECB)

    def proceed(self, data):
        obj = self.decrypt(data)
        return self.encrypt(obj)