# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount


class PremiumTo(MultiAccount):
    __name__ = "PremiumTo"
    __type__ = "account"
    __version__ = "0.21"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Premium.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.net"),
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://premium.to/API.html
    API_URL = "http://api.premium.to/api/2/"

    def api_request(self, method, **kwargs):
        return json.loads(self.load(self.API_URL + method + ".php", get=kwargs))

    def grab_hosters(self, user, password, data):
        api_data = self.api_request("hosts", userid=user, apikey=password)
        return api_data["hosts"] if api_data.get("code") == 200 else []

    def grab_info(self, user, password, data):
        api_data = self.api_request("traffic", userid=user, apikey=password)

        if api_data.get("code") == 200:
            trafficleft = api_data["traffic"] + api_data["specialtraffic"]
            return {"premium": True, "trafficleft": trafficleft, "validuntil": -1}

        else:
            return {"premium": False, "trafficleft": None, "validuntil": None}

    def signin(self, user, password, data):
        api_data = self.api_request("traffic", userid=user, apikey=password)

        if api_data["code"] != 200:
            self.log_warning(
                self._(
                    "Username and password for PremiumTo should be the API userid & apikey"
                )
            )
            self.log_warning(api_data["message"])
            self.fail_login()
