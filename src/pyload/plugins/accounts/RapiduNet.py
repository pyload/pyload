# -*- coding: utf-8 -*-

import json
import time

from ..base.account import BaseAccount


class RapiduNet(BaseAccount):
    __name__ = "RapiduNet"
    __type__ = "account"
    __version__ = "0.13"
    __status__ = "testing"

    __description__ = """Rapidu.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("prOq", None),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # https://rapidu.net/documentation/api/
    API_URL = "https://rapidu.net/api/"

    def api_request(self, method, **kwargs):
        json_data = self.load(self.API_URL + method + "/", post=kwargs)
        return json.loads(json_data)

    def grab_info(self, user, password, data):
        validuntil = None

        api_data = self.api_request("getAccountDetails", login=user, password=password)

        premium = True if api_data["userPremium"] == "1" else False
        if premium:
            validuntil = time.mktime(
                time.strptime(api_data["userPremiumDateEnd"], "%Y-%m-%d %H:%M:%S")
            )

        trafficleft = api_data["userTraffic"]

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        api_data = self.api_request("getAccountDetails", login=user, password=password)

        if "message" in api_data:
            self.log_error(api_data["message"]["error"])
            self.fail_login()
