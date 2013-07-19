# -*- coding: utf-8 -*-

from tests.helper.Stubs import Core
from pyload.plugins.network.CurlRequest import CurlRequest


class TestCurlRequest:

    def setUp(self):
        self.req = CurlRequest({})

    def tearDown(self):
        self.req.close()

    def test_load(self):
        self.req.load("http://pyload.org")

    def test_cookies(self):

        self.req.load("http://pyload.org", cookies=False)
        assert len(self.req.cj.values()) == 0

        self.req.load("http://pyload.org")
        assert len(self.req.cj.values()) > 0

    def test_auth(self):

        pass