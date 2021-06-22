# -*- coding: utf-8 -*-

import json
from binascii import b2a_hex

from beaker.crypto.pbkdf2 import pbkdf2
from pyload.core.network.request_factory import get_url

from ..base.account import BaseAccount


class PBKDF2:
    def __init__(self, passphrase, salt, iterations=1000):
        self.passphrase = passphrase
        self.salt = salt
        self.iterations = iterations

    def hexread(self, octets):
        return b2a_hex(pbkdf2(self.passphrase, self.salt, self.iterations, octets))


class OboomCom(BaseAccount):
    __name__ = "OboomCom"
    __type__ = "account"
    __version__ = "0.34"
    __status__ = "testing"

    __description__ = """Oboom.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stanley", "stanley.foerster@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    #: See https://www.oboom.com/api
    API_URL = "https://%s.oboom.com/1/"

    @classmethod
    def api_request(cls, subdomain, method, args={}):
        return json.loads(get_url(cls.API_URL % subdomain + method, post=args))

    def grab_info(self, user, password, data):
        salt = password[::-1]
        pbkdf2 = PBKDF2(password, salt, 1000).hexread(16)

        res = self.api_request("www", "login", {"auth": user, "pass": pbkdf2})

        user_data = res[1]["user"]

        premium = user_data["premium"] != "null"

        if user_data["premium_unix"] == "null":
            validuntil = -1

        else:
            validuntil = float(user_data["premium_unix"])

        trafficleft = user_data["traffic"]["current"]

        data["session"] = res[1]["session"]

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        salt = password[::-1]
        pbkdf2 = PBKDF2(password, salt, 1000).hexread(16)

        res = self.api_request("www", "login", {"auth": user, "pass": pbkdf2})

        if res[0] != 200:
            self.fail_login(res[1])
