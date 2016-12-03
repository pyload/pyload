# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from tests.helper.Stubs import Core
from pyload.plugins.network.CurlRequest import CurlRequest

from unittest import TestCase


class TestCurlRequest(TestCase):
    # This page provides a test which prints all set cookies
    cookieURL = "http://forum.pyload.org"

    def setUp(self):
        self.req = CurlRequest({})

    def tearDown(self):
        self.req.close()

    def test_load(self):
        self.req.load("http://pyload.org")

    def test_cookies(self):
        self.req.load(self.cookieURL, cookies=False)
        assert len(self.req.cj) == 0

        self.req.load(self.cookieURL)
        assert len(self.req.cj) > 1

        cookies = dict([c.strip().split(":") for c in self.req.load(self.cookieURL + "/cookies.php").splitlines()])
        for k, v in cookies.items():
            self.assertIn(k, self.req.cj)
            self.assertEqual(v, self.req.cj[k].value)

        for c in self.req.cj:
            self.assertIn(c, cookies)

        cookies = self.req.load(self.cookieURL + "/cookies.php", cookies=False)
        self.assertEqual(cookies, "")


    def test_auth(self):
        pass
