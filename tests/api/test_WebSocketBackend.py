# -*- coding: utf-8 -*-

from nose.tools import raises

from pyload.remote.apitypes import Forbidden
from pyload.remote.WSClient import WSClient

class TestWebSocketBackend:

    def setUp(self):
        self.client = WSClient()
        self.client.connect()

    def tearDown(self):
        self.client.close()

    def test_login(self):
        self.client.login("User", "test")
        self.client.getServerVersion()
        self.client.logout()

    def test_wronglogin(self):
        ret = self.client.login("WrongUser", "wrongpw")
        assert ret == False

    @raises(Forbidden)
    def test_access(self):
        self.client.getServerVersion()

    @raises(AttributeError)
    def test_unknown_method(self):
        self.client.login("User", "test")
        self.client.sdfdsg()
