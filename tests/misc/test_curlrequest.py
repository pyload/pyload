# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from unittest import TestCase

from pyload.plugins.network.curlrequest import CurlRequest
from tests.helper.stubs import Core


class TestCurlRequest(TestCase):
    # This page provides a test which prints all set cookies
    cookie_url = "https://pyload.net"

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

        cookies = dict(c.strip().split(":") for c in self.req.load(
            self.cookie_url + "/cookies.php").splitlines())
        for k, v in cookies.items():
            self.assert_int(k, self.req.cj)
            self.assertEqual(v, self.req.cj[k].value)

        for c in self.req.cj:
            self.assert_int(c, cookies)

        cookies = self.req.load(
            self.cookie_url + "/cookies.php", cookies=False)
        self.assertEqual(cookies, "")

    def test_auth(self):
        raise NotImplementedError
