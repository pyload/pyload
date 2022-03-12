# -*- coding: utf-8 -*-
import json
import time

from ..base.account import BaseAccount


class NitroflareCom(BaseAccount):
    __name__ = "NitroflareCom"
    __type__ = "account"
    __version__ = "0.21"
    __status__ = "testing"

    __description__ = """Nitroflare.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://nitroflare.com/member?s=general-api
    API_URL = "https://nitroflare.com/api/v2/"

    def api_request(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def grab_info(self, user, password, data):
        validuntil = -1
        trafficleft = None
        premium = False

        api_data = self.api_request("getKeyInfo", user=user, premiumKey=password)

        if api_data["type"] == "success":
            trafficleft = self.parse_traffic(api_data["result"]["trafficLeft"], "byte")
            premium = api_data["result"]["status"] == "active"

            if premium:
                validuntil = time.mktime(
                    time.strptime(api_data["result"]["expiryDate"], "%Y-%m-%d %H:%M:%S")
                )

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        api_data = self.api_request("getKeyInfo", user=user, premiumKey=password)

        if api_data["type"] != "success":
            error_code = api_data["code"]

            if error_code != 12:
                self.log_error(api_data["message"])
                self.fail_login()

            else:
                self.fail_login(self._("Account Login Requires Recaptcha"))
