# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from os import stat

from unittest import TestCase

from tests.helper.stubs import Core
from pyload.network.bucket import Bucket
from pyload.plugins.network.curlrequest import CurlRequest
from pyload.plugins.network.curldownload import CurlDownload


class TestCurlRequest(TestCase):

    cookie_url = "https://pyload.net"

    def setUp(self):
        self.dl = CurlDownload(Bucket())

    def tearDown(self):
        self.dl.close()

    def test_download(self):

        assert self.dl.context is not None

        self.dl.download("https://pyload.net/lib/tpl/pyload/images/pyload-logo-edited3.5-new-font-small.png", "/tmp/random.bin")

        print(self.dl.size, self.dl.arrived)
        assert self.dl.size == self.dl.arrived > 0
        assert stat("/tmp/random.bin").st_size == self.dl.size

    def test_cookies(self):

        req = CurlRequest({})
        req.load(self.cookie_url)

        assert len(req.cj) > 0

        dl = CurlDownload(Bucket(), req)

        assert req.context is dl.context is not None

        dl.download(self.cookie_url + "/cookies.php", "cookies.txt")
        with open("cookies.txt", "rb") as f:
            cookies = f.read().splitlines()

        self.assertEqual(len(cookies), len(dl.context))
        for c in cookies:
            k, v = c.strip().split(":")
            self.assert_int(k, req.cj)


    def test_attributes(self):
        assert self.dl.size == 0
        assert self.dl.speed == 0
        assert self.dl.arrived == 0
