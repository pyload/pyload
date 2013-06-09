# -*- coding: utf-8 -*-

from nose.tools import raises, assert_equal

from requests.auth import HTTPBasicAuth
import requests

import json

from pyload.remote.apitypes import Forbidden
from pyload.remote.JSONClient import JSONClient


class TestJSONBackend:
    login = ("User", "pwhere")

    def setUp(self):
        self.client = JSONClient()

    def test_login(self):
        self.client.login(*self.login)
        self.client.getServerVersion()
        self.client.logout()

    def test_wronglogin(self):
        ret = self.client.login("WrongUser", "wrongpw")
        assert ret is False


    def test_httpauth(self):
        # cheap http auth
        ret = requests.get(self.client.URL + "/getServerVersion", auth=HTTPBasicAuth(*self.login))
        assert_equal(ret.status_code, 200)
        assert ret.text

    def test_jsonbody(self):
        payload = {'section': 'webinterface', 'option': 'port'}
        headers = {'content-type': 'application/json'}

        ret = requests.get(self.client.URL + "/getConfigValue", headers=headers,
                           auth=HTTPBasicAuth(*self.login), data=json.dumps(payload))

        assert_equal(ret.status_code, 200)
        assert ret.text

    @raises(Forbidden)
    def test_access(self):
        self.client.getServerVersion()

    @raises(AttributeError)
    def test_unknown_method(self):
        self.client.login(*self.login)
        self.client.sdfdsg()