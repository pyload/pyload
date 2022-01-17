# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount


class FastixRu(MultiAccount):
    __name__ = "FastixRu"
    __type__ = "account"
    __version__ = "0.13"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Fastix account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Massimo Rosamilia", "max@spiritix.eu")]

    def grab_hosters(self, user, password, data):
        html = self.load(
            "http://fastix.ru/api_v2",
            get={
                "apikey": "5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y",
                "sub": "allowed_sources",
            },
        )
        host_list = json.loads(html)
        host_list = host_list["allow"]
        return host_list

    def grab_info(self, user, password, data):
        html = self.load(
            "http://fastix.ru/api_v2/",
            get={"apikey": data["apikey"], "sub": "getaccountdetails"},
        )
        json_data = json.loads(html)

        points = json_data["points"]
        trafficleft = float(points) * 1024 ** 2

        if points > 0:
            account_info = {"validuntil": -1, "trafficleft": trafficleft}
        else:
            account_info = {"validuntil": None, "trafficleft": None, "premium": False}
        return account_info

    def signin(self, user, password, data):
        html = self.load(
            "https://fastix.ru/api_v2/",
            get={"sub": "get_apikey", "email": user, "password": password},
        )
        api = json.loads(html)

        if "error" in api:
            self.fail_login(api["error_txt"])

        else:
            data["apikey"] = api["apikey"]
