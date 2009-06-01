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
    def __init__(self, client, pw):
        self.client = client
        key = hashlib.sha256(pw)
        self.bf = Blowfish.new(key.hexdigest(), Blowfish.MODE_ECB)

    def proceed(self, data):
        obj = self.decrypt(data)

        self.client.data_arrived(obj)