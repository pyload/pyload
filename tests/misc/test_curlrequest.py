# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from tests.helper.stubs import Core
from pyload.plugins.network.curlrequest import CurlRequest

from unittest import TestCase


class TestCurlRequest(TestCase):
    # This page provides a test which prints all set cookies
    cookieURL = "https://pyload.net"

    def setUp(self):
        self.req = CurlRequest({})

    def tearDown(self):
        self.req.close()

    def test_load(self):
        self.req.load("https://pyload.net")

    def test_cookies(self):
        self.req.load(self.cookie_url, cookies=False)
        assert len(self.req.cj) == 0

        self.req.load(self.cookie_url)
        assert len(self.req.cj) > 1

        cookies = dict(c.strip().split(":") for c in self.req.load(self.cookie_url + "/cookies.php").splitlines())
        for k, v in cookies.items():
            self.assert_in(k, self.req.cj)
            self.assert_equal(v, self.req.cj[k].value)

        for c in self.req.cj:
            self.assert_in(c, cookies)

        cookies = self.req.load(self.cookie_url + "/cookies.php", cookies=False)
        self.assert_equal(cookies, "")


    def test_auth(self):
        pass
