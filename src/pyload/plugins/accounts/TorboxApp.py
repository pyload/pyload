# -*- coding: utf-8 -*-

import json
import time
from functools import reduce

import pycurl

from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_account import MultiAccount


class TorboxApp(MultiAccount):
    __name__ = "TorboxApp"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
        (
            "ignore_status",
            "bool",
            "Treat all hosters as available (ignore status field)",
            False,
        ),
    ]

    __description__ = """Torbox.app account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    # See https://api-docs.torbox.app/
    API_URL = "https://api.torbox.app/v1/api/"

    def api_request(self, method, api_key=None, get=None, post=None):
        if api_key is not None:
            self.req.http.set_header("Authorization", f"Bearer {api_key}")

        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)
        except BadHeader as exc:
            json_data = exc.content

        api_data = json.loads(json_data)
        return api_data

    def grab_hosters(self, user, password, data):
        api_data = self.api_request("webdl/hosters", api_key=password)
        if not api_data.get("success", False):
            self.log_error(api_data["detail"])
            return []

        else:
            hosts = reduce(
                lambda x, y: x + y,
                [
                    h["domains"]
                    for h in api_data["data"]
                    if h["status"] is True
                ],
            )

            return hosts

    def grab_info(self, user, password, data):
        validuntil = -1
        premium = False

        api_data = self.api_request("user/me", api_key=password)
        if not api_data.get("success", False):
            self.log_error(api_data["detail"])

        else:
            premium = api_data["data"]["plan"] > 0
            if premium:
                validuntil = time.mktime(
                    time.strptime(api_data["data"]["premium_expires_at"], "%Y-%m-%dT%H:%M:%SZ")
                ) - time.timezone

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        api_data = self.api_request("user/me", api_key=password)
        if api_data.get("success", False):
            if api_data["data"]["email"] != user:
                self.log_error(self._("Username for TorboxApp should be your torbox.app email"))
                self.fail_login()

        else:
            self.log_error(self._("Password for TorboxApp should be your torbox.app API token"))
            self.log_error(api_data["detail"])
            self.fail_login()
