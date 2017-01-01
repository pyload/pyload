# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import object
from tests.helper.stubs import Core

from pyload.plugins.network.curlrequest import CurlRequest
from pyload.network.request import RequestFactory


class TestRequestFactory(object):

    @classmethod
    def setUpClass(cls):
        cls.req = RequestFactory(Core())

    def test_get_request(self):
        req = self.req.get_request()

        new_req = self.req.get_request(req.get_context())
        assert new_req.get_context() == req.get_context()

        cj = CurlRequest.CONTEXT_CLASS()
        assert self.req.get_request(cj).context is cj

    def test_get_request_class(self):

        self.req.get_request(None, CurlRequest)

    def test_get_download(self):
        dl = self.req.get_download_request()
        dl.close()

        # with given request
        req = self.req.get_request()
        dl = self.req.get_download_request(req)

        assert req.context is dl.context
        assert req.options is dl.options

        dl.close()
