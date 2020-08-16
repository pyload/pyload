# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount


class PremiumizeMe(MultiAccount):
    __name__ = "PremiumizeMe"
    __type__ = "account"
    __version__ = "0.30"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Premiumize.me account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Florian Franzen", "FlorianFranzen@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://www.premiumize.me/static/api/api.html
    API_URL = "https://api.premiumize.me/pm-api/v1.php"

    def api_respond(self, method, user, password, **kwargs):
        get_params = {"method": method, "params[login]": user, "params[pass]": password}
        for key, val in kwargs.items():
            get_params["params[{}]".format(key)] = val

        json_data = self.load(self.API_URL, get=get_params)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        res = self.api_respond("hosterlist", user, password)

        if res["status"] != 200:
            return []

        return res["result"]["tldlist"]

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = False

        res = self.api_respond("accountstatus", user, password)

        if res["status"] == 200:
            validuntil = float(res["result"]["expires"])

            # TODO: Remove `>> 10` in 0.6.x
            trafficleft = max(0, res["result"]["trafficleft_bytes"] >> 10)

            if res["result"]["type"] != "free":
                premium = True

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        res = self.api_respond("accountstatus", user, password)

        if res["status"] != 200:
            self.fail_login(res["statusmessage"])
