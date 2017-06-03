# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import object
from contextlib import closing

from future import standard_library

from pyload.core.network.factory import RequestFactory
from pyload.requests.curl.request import CurlRequest
from tests.helper.stubs import Core

standard_library.install_aliases()


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
        with closing(self.req.get_download_request(req)) as dl:
            assert req.context is dl.context
            assert req.options is dl.options
