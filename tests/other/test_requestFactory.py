# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import object
from tests.helper.stubs import Core

from pyload.plugins.network.curlrequest import CurlRequest
from pyload.network.requestfactory import RequestFactory


class TestRequestFactory(object):

    @classmethod
    def setUpClass(cls):
        cls.req = RequestFactory(Core())

    def test_get_request(self):
        req = self.req.getRequest()

        new_req = self.req.getRequest(req.getContext())
        assert new_req.getContext() == req.getContext()

        cj = CurlRequest.CONTEXT_CLASS()
        assert self.req.getRequest(cj).context is cj

    def test_get_request_class(self):

        self.req.getRequest(None, CurlRequest)

    def test_get_download(self):
        dl = self.req.getDownloadRequest()
        dl.close()

        # with given request
        req = self.req.getRequest()
        dl = self.req.getDownloadRequest(req)

        assert req.context is dl.context
        assert req.options is dl.options

        dl.close()
