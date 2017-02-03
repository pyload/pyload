# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import object
from nose.tools import raises, assertEqual

from requests.auth import HTTPBasicAuth
import requests

import json

from pyload.remote.apitypes import Forbidden
from pyload.remote.JSONClient import JSONClient

from tests.helper.config import credentials, webaddress


class TestJSONBackend(object):

    def setUp(self):
        self.client = JSONClient(webaddress)

    def test_login(self):
        self.client.login(*credentials)
        self.client.get_server_version()
        self.client.logout()

    def test_wronglogin(self):
        ret = self.client.login("WrongUser", "wrongpw")
        assert ret is False

    def test_httpauth(self):
        # cheap http auth
        ret = requests.get(webaddress + "/getServerVersion",
                           auth=HTTPBasicAuth(*credentials))
        assertEqual(ret.status_code, 200)
        assert ret.text

    def test_jsonbody(self):
        payload = {'section': 'webinterface', 'option': 'port'}
        headers = {'content-type': 'application/json'}

        ret = requests.get(webaddress + "/getConfigValue", headers=headers,
                           auth=HTTPBasicAuth(*credentials), data=json.dumps(payload))

        assertEqual(ret.status_code, 200)
        assert ret.text

    @raises(Forbidden)
    def test_access(self):
        self.client.get_server_version()

    @raises(AttributeError)
    def test_unknown_method(self):
        self.client.login(*credentials)
        self.client.sdfdsg()
