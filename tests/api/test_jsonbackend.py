# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import object
from nose.tools import raises, assert_equal

from requests.auth import HTTPBasicAuth
import requests

import json

from pyload.remote.apitypes import Forbidden
from pyload.remote.JSONClient import JSONClient

from tests.helper.config import credentials, webAddress


class TestJSONBackend(object):

    def setUp(self):
        self.client = JSONClient(webAddress)

    def test_login(self):
        self.client.login(*credentials)
        self.client.getServerVersion()
        self.client.logout()

    def test_wronglogin(self):
        ret = self.client.login("WrongUser", "wrongpw")
        assert ret is False

    def test_httpauth(self):
        # cheap http auth
        ret = requests.get(webAddress + "/getServerVersion", auth=HTTPBasicAuth(*credentials))
        assert_equal(ret.status_code, 200)
        assert ret.text

    def test_jsonbody(self):
        payload = {'section': 'webinterface', 'option': 'port'}
        headers = {'content-type': 'application/json'}

        ret = requests.get(webAddress + "/getConfigValue", headers=headers,
                           auth=HTTPBasicAuth(*credentials), data=json.dumps(payload))

        assert_equal(ret.status_code, 200)
        assert ret.text

    @raises(Forbidden)
    def test_access(self):
        self.client.getServerVersion()

    @raises(AttributeError)
    def test_unknown_method(self):
        self.client.login(*credentials)
        self.client.sdfdsg()
