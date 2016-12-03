# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.remote.JSONClient import JSONClient
from pyload.remote.WSClient import WSClient

from tests.helper.config import webAddress, wsAddress

from .ApiProxy import ApiProxy

class ApiTester:

    tester= []

    @classmethod
    def register(cls, tester):
        cls.tester.append(tester)

    @classmethod
    def get_methods(cls):
        """ All available methods for testing """
        methods = []
        for t in cls.tester:
            methods.extend(getattr(t, attr) for attr in dir(t) if attr.startswith("test_"))
        return methods

    def __init__(self):
        ApiTester.register(self)
        self.api = None

    def setApi(self, api):
        self.api = api

    def enableJSON(self):
        self.api = ApiProxy(JSONClient(webAddress))

    def enableWS(self):
        self.api = ApiProxy(WSClient(wsAddress))
