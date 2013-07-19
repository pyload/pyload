# -*- coding: utf-8 -*-

from os import stat
from os.path import exists

from tests.helper.Stubs import Core
from pyload.network.Bucket import Bucket
from pyload.plugins.network.CurlDownload import CurlDownload

class TestCurlRequest:

    def setUp(self):
        self.dl = CurlDownload(Bucket())

    def tearDown(self):
        self.dl.close()

    def test_download(self):

        self.dl.download("http://pyload.org/lib/tpl/pyload/images/pyload-logo-edited3.5-new-font-small.png", "/tmp/random.bin")

        print self.dl.size, self.dl.arrived
        assert self.dl.size == self.dl.arrived > 0
        assert stat("/tmp/random.bin").st_size == self.dl.size


    def test_attributes(self):
        assert self.dl.size == 0
        assert self.dl.speed == 0
        assert self.dl.arrived == 0