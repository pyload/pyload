# -*- coding: utf-8 -*-

from __future__ import print_function
from os import stat

from unittest import TestCase

from tests.helper.Stubs import Core
from pyload.network.Bucket import Bucket
from pyload.plugins.network.CurlRequest import CurlRequest
from pyload.plugins.network.CurlDownload import CurlDownload

class TestCurlRequest(TestCase):

    cookieURL = "http://forum.pyload.org"

    def setUp(self):
        self.dl = CurlDownload(Bucket())

    def tearDown(self):
        self.dl.close()

    def test_download(self):

        assert self.dl.context is not None

        self.dl.download("http://pyload.org/lib/tpl/pyload/images/pyload-logo-edited3.5-new-font-small.png", "/tmp/random.bin")

        print(self.dl.size, self.dl.arrived)
        assert self.dl.size == self.dl.arrived > 0
        assert stat("/tmp/random.bin").st_size == self.dl.size

    def test_cookies(self):

        req = CurlRequest({})
        req.load(self.cookieURL)

        assert len(req.cj) > 0

        dl = CurlDownload(Bucket(), req)

        assert req.context is dl.context is not None

        dl.download(self.cookieURL + "/cookies.php", "cookies.txt")
        cookies = open("cookies.txt", "rb").read().splitlines()

        self.assertEqual(len(cookies), len(dl.context))
        for c in cookies:
            k, v = c.strip().split(":")
            self.assertIn(k, req.cj)


    def test_attributes(self):
        assert self.dl.size == 0
        assert self.dl.speed == 0
        assert self.dl.arrived == 0
