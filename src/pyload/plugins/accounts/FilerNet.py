# -*- coding: utf-8 -*-
import json
import time

from pyload.core.network.http.exceptions import BadHeader

from ..base.account import BaseAccount


class FilerNet(BaseAccount):
    __name__ = "FilerNet"
    __type__ = "account"
    __version__ = "0.17"
    __status__ = "testing"

    __description__ = """Filer.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://filer.net/api
    API_URL = "https://filer.net/api/"

    def api_request(self, method, **kwargs):
        try:
            json_data = self.load(self.API_URL + method, post=kwargs)
        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def grab_info(self, user, password, data):
        api_data = self.api_request("user/account")

        premium = api_data["status"] == "Premium"

        #: Free user
        if premium is False:
            return {"premium": False, "validuntil": None, "trafficleft": None}

        validuntil = time.mktime(time.strptime(api_data["premiumUntil"], "%Y-%m-%dT%H:%M:%S%z"))
        trafficleft = self.parse_traffic(api_data["traffic"])

        return {"premium": premium, "validuntil": validuntil, "trafficleft": trafficleft}

    def signin(self, user, password, data):
        api_data = self.api_request("user/account")
        if "message" not in api_data:
            self.skip_login()

        api_data = self.api_request("user/login", email=user, password=password)
        if api_data.get("message", "") != "Login successful":
            self.log_error(api_data["message"])
            self.fail_login()
