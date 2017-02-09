# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from builtins import object
from urllib.parse import urlencode
from urllib.request import urlopen

from future import standard_library
from http.client import FORBIDDEN, UNAUTHORIZED

from pyload.remote.apitypes import Forbidden, Unauthorized
from pyload.remote.json_converter import dumps, loads

standard_library.install_aliases()



class JSONClient(object):
    URL = "http://localhost:8010/api"

    def __init__(self, url=None):
        self.url = url or self.URL
        self.session = None

    def request(self, path, data):
        ret = urlopen(self.url + path, urlencode(data))
        if ret.code == 400:
            raise loads(ret.read())
        if ret.code == 404:
            raise AttributeError("Unknown Method")
        if ret.code == 500:
            raise Exception("Remote Exception")
        if ret.code == UNAUTHORIZED:
            raise Unauthorized
        if ret.code == FORBIDDEN:
            raise Forbidden
        return ret.read()

    def login(self, username, password):
        self.session = loads(self.request(
            "/login", {'username': username, 'password': password}))
        return self.session

    def logout(self):
        self.call("logout")
        self.session = None

    def call(self, func, *args, **kwargs):
        # Add the current session
        kwargs['session'] = self.session
        path = "/{}/{}".format(func, "/".join(dumps(x) for x in args))
        data = dict((k, dumps(v)) for k, v in kwargs.items())
        rep = self.request(path, data)
        return loads(rep)

    def __getattr__(self, item):
        def call(*args, **kwargs):
            return self.call(item, *args, **kwargs)

        return call

# if __name__ == "__main__":
    # api = JSONClient()
    # api.login("User", "test")
    # print(api.get_server_version())
