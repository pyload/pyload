# -*- coding: utf-8 -*-
try:
    from urllib import urlencode
    from urllib2 import urlopen, HTTPError
except ImportError:
    from urllib.parse import urlencode
    from urllib.request import urlopen
    from urllib.error import HTTPError

from json import loads

from logging import log

url = "http://localhost:8000/api/%s"

class TestJson:

    def call(self, name, post=None):
        if not post: post = {}
        post["session"] = self.key
        u = urlopen(url % name, data=urlencode(post).encode('utf-8'))
        return loads(u.read())

    def setUp(self):
        u = urlopen(url % "login", data=urlencode({"username": "TestUser", "password": "pwhere"}).encode('utf-8'))
        self.key = loads(u.read())
        assert self.key is not False

    def test_wronglogin(self):
        u = urlopen(url % "login", data=urlencode({"username": "crap", "password": "wrongpw"}).encode('utf-8'))
        assert loads(u.read()) is False

    def test_access(self):
        try:
            urlopen(url % "getServerVersion")
        except HTTPError as e:
            assert e.code == 403
        else:
            assert False

    def test_status(self):
        ret = self.call("statusServer")
        log(1, str(ret))
        assert "pause" in ret
        assert "queue" in ret

    def test_unknown_method(self):
        try:
            self.call("notExisting")
        except HTTPError as e:
            assert e.code == 404
        else:
            assert False