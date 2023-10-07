# -*- coding: utf-8 -*-

import json
from functools import reduce

from ..base.multi_account import MultiAccount


class AlldebridCom(MultiAccount):
    __name__ = "AlldebridCom"
    __type__ = "account"
    __version__ = "0.46"
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
        ("streams_also", "bool", "Also download from stream hosters", False),
    ]

    __description__ = """AllDebrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Andy Voigt", "spamsales@online.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://docs.alldebrid.com/
    API_URL = "https://api.alldebrid.com/v4/"

    def api_request(self, method, get={}, post={}, multipart=False):
        get.update({"agent": "pyLoad", "version": self.pyload.version})
        json_data = json.loads(
            self.load(self.API_URL + method, get=get, post=post, multipart=multipart)
        )
        if json_data["status"] == "success":
            return json_data["data"]
        else:
            return json_data

    def grab_hosters(self, user, password, data):
        api_data = self.api_request("user/hosts", get={"apikey": password})
        if api_data.get("error", False):
            self.log_error(api_data["error"]["message"])
            return []

        else:
            valid_statuses = (
                (True, False) if self.config.get("ignore_status") is True else (True,)
            )
            valid_hosters = list(api_data["hosts"].values()) + (
                list(api_data["streams"].values())
                if self.config.get("streams_also") is True
                else []
            )
            hosts = reduce(
                lambda x, y: x + y,
                [
                    _h["domains"]
                    for _h in valid_hosters
                    if _h.get("status", False) in valid_statuses
                    or _h.get("type") == "free"
                ],
            )
            return hosts

    def grab_info(self, user, password, data):
        api_data = self.api_request("user", get={"apikey": password})

        if api_data.get("error", False):
            self.log_error(api_data["error"]["message"])
            premium = False
            validuntil = -1

        else:
            premium = api_data["user"]["isPremium"]
            validuntil = api_data["user"]["premiumUntil"] or -1

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        api_data = self.api_request("user", get={"apikey": password})

        if api_data.get("error", False):
            self.log_error(
                self._(
                    "Password for alldebrid.com should be the API token - use GetAlldebridTokenV4.py to get it: https://github.com/pyload/pyload/files/4489732/GetAlldebridTokenV4.zip"
                )
            )
            self.fail_login(api_data["error"]["message"])

        elif api_data["user"]["username"] != user:
            self.log_error(
                self._(
                    "username for alldebrid.com should be your alldebrid.com username"
                )
            )
            self.fail_login()
