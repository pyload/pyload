# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount
from ..helpers import set_cookie


class SimplyPremiumCom(MultiAccount):
    __name__ = "SimplyPremiumCom"
    __type__ = "account"
    __version__ = "0.15"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Simply-Premium.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("EvolutionClip", "evolutionclip@live.de")]

    def grab_hosters(self, user, password, data):
        json_data = self.load(
            "https://www.simply-premium.com/api/hosts.php",
            get={"format": "json", "online": 1},
        )
        json_data = json.loads(json_data)

        host_list = [element["regex"] for element in json_data["result"]]

        return host_list

    def grab_info(self, user, password, data):
        premium = False
        validuntil = -1
        trafficleft = None

        json_data = self.load("https://www.simply-premium.com/api/user.php?format=json")

        self.log_debug(f"JSON data: {json_data}")

        json_data = json.loads(json_data)

        if "vip" in json_data["result"] and json_data["result"]["vip"]:
            premium = True

        if "timeend" in json_data["result"] and json_data["result"]["timeend"]:
            validuntil = float(json_data["result"]["timeend"])

        if (
            "remain_traffic" in json_data["result"]
            and json_data["result"]["remain_traffic"]
        ):
            trafficleft = float(json_data["result"]["remain_traffic"])

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        set_cookie(self.req.cj, "simply-premium.com", "lang", "EN")

        html = self.load(
            "https://www.simply-premium.com/login.php",
            post={"key": user}
            if not password
            else {"login_name": user, "login_pass": password},
        )

        if "logout" not in html:
            self.fail_login()
