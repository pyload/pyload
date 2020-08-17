# -*- coding: utf-8 -*-

import json
from functools import reduce

from ..base.multi_account import MultiAccount


class AlldebridCom(MultiAccount):
    __name__ = "AlldebridCom"
    __type__ = "account"
    __version__ = "0.41"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """AllDebrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Andy Voigt", "spamsales@online.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://docs.alldebrid.com/
    API_URL = "https://api.alldebrid.com/"

    def api_response(self, method, **kwargs):
        kwargs["agent"] = "pyLoad"
        kwargs["version"] = self.pyload.version
        html = self.load(self.API_URL + method, get=kwargs)
        return json.loads(html)

    def grab_hosters(self, user, password, data):
        json_data = self.api_response("user/hosts", token=data["token"])
        if json_data.get("error", False):
            return []

        else:
            return reduce(
                lambda x, y: x + y,
                [
                    [h["domain"]] + h.get("altDomains", [])
                    for h in json_data["hosts"].values()
                    if h["status"] is True
                ],
            )

    def grab_info(self, user, password, data):
        json_data = self.api_response("user/login", token=data["token"])

        if json_data.get("error", False):
            premium = False
            validuntil = -1

        else:
            premium = json_data["user"]["isPremium"]
            validuntil = json_data["user"]["premiumUntil"] or -1

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        json_data = self.api_response("user/login", username=user, password=password)

        if json_data.get("error", False):
            self.fail_login(json_data["error"])

        else:
            data["token"] = json_data["token"]
