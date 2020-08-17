# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount


class HighWayMe(MultiAccount):
    __name__ = "HighWayMe.py"
    __type__ = "account"
    __version__ = "0.10"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """High-Way.me account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("EvolutionClip", "evolutionclip@live.de")]

    def grab_hosters(self, user, password, data):
        html = self.load("https://high-way.me/api.php", get={"hoster": 1})
        json_data = json.loads(html)
        return [element["name"] for element in json_data["hoster"]]

    def grab_info(self, user, password, data):
        premium = False
        validuntil = -1
        trafficleft = None

        json_data = self.load("https://high-way.me/api.php?user")

        self.log_debug(f"JSON data: {json_data}")

        json_data = json.loads(json_data)

        if "premium" in json_data["user"] and json_data["user"]["premium"]:
            premium = True

        if "premium_bis" in json_data["user"] and json_data["user"]["premium_bis"]:
            validuntil = float(json_data["user"]["premium_bis"])

        if (
            "premium_traffic" in json_data["user"]
            and json_data["user"]["premium_traffic"]
        ):
            # TODO: Remove `>> 10` in 0.6.x
            trafficleft = float(json_data["user"]["premium_traffic"]) >> 10

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        html = self.load(
            "https://high-way.me/api.php?login",
            post={"login": "1", "user": user, "pass": password},
        )

        if "UserOrPassInvalid" in html:
            self.fail_login()
