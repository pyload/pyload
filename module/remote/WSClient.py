#!/usr/bin/env python
# -*- coding: utf-8 -*-

from websocket import create_connection
from httplib import UNAUTHORIZED, FORBIDDEN

from json_converter import loads, dumps
from ttypes import Unauthorized, Forbidden

class WSClient:
    URL = "ws://localhost:7227/api"

    def __init__(self, url=None):
        self.url = url or self.URL
        self.ws =  None

    def connect(self):
        self.ws = create_connection(self.URL)

    def close(self):
        self.ws.close()

    def login(self, username, password):
        if not self.ws: self.connect()
        return self.call("login", username, password)

    def call(self, func, *args, **kwargs):
        if not self.ws:
            raise Exception("Not Connected")

        if kwargs:
            self.ws.send(dumps([func, args, kwargs]))
        else: # omit kwargs
            self.ws.send(dumps([func, args]))

        code, result = loads(self.ws.recv())
        if code == 400:
            raise result
        if code == 404:
            raise AttributeError("Unknown Method")
        elif code == 500:
            raise Exception("Remote Exception: %s" % result)
        elif code == UNAUTHORIZED:
            raise Unauthorized()
        elif code == FORBIDDEN:
            raise Forbidden()

        return result

    def __getattr__(self, item):
        def call(*args, **kwargs):
            return self.call(item, *args, **kwargs)

        return call

if __name__ == "__main__":
    api = WSClient()
    api.login("User", "test")
    print api.getServerVersion()