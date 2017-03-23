# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import object

from future import standard_library
standard_library.install_aliases()

from pyload.rpc.jsonclient import JSONClient
from pyload.rpc.wsclient import WSClient
from tests.api.apiproxy import ApiProxy
from tests.helper.config import webaddress, wsaddress


class ApiTester(object):

    tester = []

    @classmethod
    def register(cls, tester):
        cls.tester.append(tester)

    @classmethod
    def get_methods(cls):
        """
        All available methods for testing.
        """
        methods = []
        for t in cls.tester:
            methods.extend(getattr(t, attr)
                           for attr in dir(t) if attr.startswith("test_"))
        return methods

    def __init__(self):
        ApiTester.register(self)
        self.api = None

    def set_api(self, api):
        self.api = api

    def enable_json(self):
        self.api = ApiProxy(JSONClient(webaddress))

    def enable_ws(self):
        self.api = ApiProxy(WSClient(wsaddress))
