# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import object

from future import standard_library

from nose.tools import raises
from pyload.core.datatype import Forbidden
from pyload.rpc.wsclient import WSClient
from tests.helper.config import credentials, wsaddress

standard_library.install_aliases()


class TestWebSocketBackend(object):

    def setUp(self):
        self.client = WSClient(wsaddress)
        self.client.connect()

    def tearDown(self):
        self.client.close()

    def test_login(self):
        self.client.login(*credentials)
        self.client.get_server_version()
        self.client.logout()

    def test_wronglogin(self):
        ret = self.client.login("WrongUser", "wrongpw")
        assert ret is False

    @raises(Forbidden)
    def test_access(self):
        self.client.get_server_version()

    @raises(AttributeError)
    def test_unknown_method(self):
        self.client.login(*credentials)
        self.client.sdfdsg()
