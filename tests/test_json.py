# -*- coding: utf-8 -*-

from builtins import object, str
from json import loads
from logging import log
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

from pyload.core.api import __version__ as API_VERSION

url = "http://localhost:8000/api/v{}/{{}}".format(API_VERSION)


class TestJson:
    def call(self, name, post=None):
        if not post:
            post = {}
        post["session"] = self.key
        u = urlopen(url.format(name), data=urlencode(post))
        return loads(u.read())

    def setUp(self):
        u = urlopen(
            url.format("login"),
            data=urlencode({"username": "TestUser", "password": "pwhere"}),
        )
        self.key = loads(u.read())
        assert self.key is not False

    def test_wronglogin(self):
        u = urlopen(
            url.format("login"),
            data=urlencode({"username": "crap", "password": "wrongpw"}),
        )
        assert loads(u.read()) is False

    def test_access(self):
        try:
            urlopen(url.format("getServerVersion"))
        except HTTPError as exc:
            assert exc.code == 403
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
        except HTTPError as exc:
            assert exc.code == 404
        else:
            assert False
