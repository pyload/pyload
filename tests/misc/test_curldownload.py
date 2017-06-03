# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os

from future import standard_library

from pyload.requests.bucket import Bucket
from pyload.requests.curl.download import CurlDownload
from pyload.requests.curl.request import CurlRequest
from pyload.utils.fs import lopen
# needed to register globals
from tests.helper import stubs
from unittest2 import TestCase

standard_library.install_aliases()


class TestCurlRequest(TestCase):

    cookie_url = "https://pyload.net"

    def setUp(self):
        self.dl = CurlDownload(Bucket())

    def tearDown(self):
        self.dl.close()

    def test_download(self):

        assert self.dl.context is not None

        self.dl.download(
            "https://pyload.net/lib/tpl/pyload/images/pyload-logo-edited3.5-new-font-small.png",
            "/tmp/random.bin")

        print(self.dl.size, self.dl.arrived)
        assert self.dl.size == self.dl.arrived > 0
        assert os.stat("/tmp/random.bin").st_size == self.dl.size

    def test_cookies(self):

        req = CurlRequest({})
        req.load(self.cookie_url)

        assert len(req.cj) > 0

        dl = CurlDownload(Bucket(), req)

        assert req.context is dl.context is not None

        dl.download(self.cookie_url + "/cookies.php", "cookies.txt")
        with lopen("cookies.txt", mode='rb') as fp:
            cookies = fp.read().splitlines()

        self.assertEqual(len(cookies), len(dl.context))
        for c in cookies:
            k, v = c.strip().split(":")
            self.assertIn(k, req.cj)

    def test_attributes(self):
        assert self.dl.size == 0
        assert self.dl.speed == 0
        assert self.dl.arrived == 0
