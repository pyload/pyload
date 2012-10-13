#!/usr/bin/env python
# -*- coding: utf-8 -*-

from json_converter import loads, dumps
from websocket import create_connection

class WSClient:
    URL = "ws://localhost:7227/api"

    def __init__(self, url=None):
        self.url = url or self.URL
        self.ws =  None

    def login(self, username, password):
        self.ws = create_connection(self.URL)
        return self.call("login", username, password)

    def logout(self):
        self.call("logout")
        self.ws.close()

    def call(self, func, *args, **kwargs):
        self.ws.send(dumps([func, args, kwargs]))
        code, result = loads(self.ws.recv())
        if code == 404:
            raise AttributeError("Unknown Method")
        elif code == 505:
            raise Exception("Remote Exception")

        return result

    def __getattr__(self, item):
        def call(*args, **kwargs):
            return self.call(item, *args, **kwargs)

        return call

if __name__ == "__main__":
    api = WSClient()
    api.login("User", "test")
    print api.getServerVersion()