# -*- coding: utf-8 -*-

import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.account import BaseAccount


class FikperCom(BaseAccount):
    __name__ = "FikperCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Fikper.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://sapi.fikper.com/"

    # See https://sapi.fikper.com/api/reference/
    def api_request(self, method, api_key=None, **kwargs):
        if api_key is not None:
            self.req.http.c.setopt(pycurl.HTTPHEADER, [f"x-api-key: {api_key}"])

        try:
            json_data = self.load(self.API_URL + method, post=kwargs)
            return json.loads(json_data)

        except json.JSONDecodeError:
            return json_data

        except BadHeader as exc:
            return json.loads(exc.content)

    def grab_info(self, user, password, data):
        api_data = self.api_request("api/account/info", api_key=password)

        premium = api_data["accountType"] == "premium"
        if premium:
            validuntil = api_data["premiumExpire"] / 1000

        else:
            validuntil = -1

        trafficleft = api_data["totalBandwidth"] - api_data["usedBandwidth"]

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        api_data = self.api_request("api/account/info", api_key=password)
        if api_data.get("code") is not None:
            self.log_error(self._("Password for fikper.com should be the API token"))
            self.log_error(self._("API error"), api_data)
            self.fail_login()

        elif api_data["email"] != user:
            self.log_error(
                self._("username for fikper.com should be your fikper.com email")
            )
            self.fail_login()
