# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import object
from urllib.request import urlopen
from urllib.parse import urlencode
from http.client import UNAUTHORIZED, FORBIDDEN

from pyload.remote.json_converter import loads, dumps
from pyload.remote.apitypes import Unauthorized, Forbidden


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
        self.session = loads(self.request("/login", {'username': username, 'password': password}))
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
