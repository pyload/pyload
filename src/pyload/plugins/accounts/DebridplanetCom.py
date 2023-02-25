# -*- coding: utf-8 -*-

import hashlib
import json
import time

import pycurl
from pyload.core.utils.convert import to_bytes

from ..base.multi_account import MultiAccount


class DebridplanetCom(MultiAccount):
    __name__ = "DebridplanetCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Debridplanet.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://debridplanet.com/v1/"

    def api_request(self, method, **kwargs):
        token = self.info["data"].get("token")
        if token is not None:
            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Authorization: Bearer " + token]
            )
        json_data = self.load(f"{self.API_URL}{method}.php", post=json.dumps(kwargs))
        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        api_data = self.api_request("supportedhosts")
        hosts = [
            h["host"]
            for h in api_data["supportedhosts"]
            if h["currently_working"]
        ]
        return hosts

    def grab_info(self, user, password, data):
        validuntil = None
        premium = False

        api_data = self.api_request("user-info")
        if api_data.get("success", False):
            premium = api_data["user"]["account_type"] == "premium"
            validuntil = time.mktime(time.strptime(api_data["user"]["expire"], "%Y-%m-%dT%H:%M:%S"))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        api_data = self.api_request("user-info")
        if api_data.get("success", False):
            self.skip_login()

        data["token"] = None
        api_data = self.api_request("login", username=user, password=hashlib.sha256(to_bytes(password)).hexdigest())
        if api_data.get("success", False):
            data["token"] = api_data["token"]

        else:
            self.fail_login()
