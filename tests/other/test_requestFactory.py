# -*- coding: utf-8 -*-

from tests.helper.Stubs import Core

from pyload.plugins.network.CurlRequest import CurlRequest
from pyload.network.RequestFactory import RequestFactory

class TestRequestFactory:

    @classmethod
    def setUpClass(cls):
        cls.req = RequestFactory(Core())

    def test_get_request(self):
        req = self.req.getRequest()

        new_req = self.req.getRequest(req.getContext())
        assert new_req.getContext() == req.getContext()

    def test_get_request_class(self):

        self.req.getRequest(None, CurlRequest)

    def test_get_download(self):
        dl = self.req.getDownloadRequest()
        dl.close()

        # with given request
        dl = self.req.getDownloadRequest(self.req.getRequest())
        dl.close()