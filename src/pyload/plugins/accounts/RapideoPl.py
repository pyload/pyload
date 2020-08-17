# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import time

from ..base.multi_account import MultiAccount


class RapideoPl(MultiAccount):
    __name__ = "RapideoPl"
    __type__ = "account"
    __version__ = "0.10"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = "Rapideo.pl account plugin"
    __license__ = "GPLv3"
    __authors__ = [("goddie", "dev@rapideo.pl")]

    API_URL = "http://enc.rapideo.pl"
    API_QUERY = {
        "site": "newrd",
        "username": "",
        "password": "",
        "output": "json",
        "loc": "1",
        "info": "1",
    }

    def grab_hosters(self, user, password, data):
        html = self.load("https://www.rapideo.pl/clipboard.php?json=3").strip()
        hostings = json.loads(html)
        hostings_domains = [
            domain
            for row in hostings
            for domain in row["domains"]
            if row["sdownload"] == "0"
        ]
        self.log_debug(hostings_domains)
        return hostings_domains

    def grab_info(self, user, password, data):
        try:
            result = json.loads(self.run_auth_query())

        except Exception:
            # TODO: return or let it be thrown?
            return

        premium = False
        valid_untill = -1

        if "expire" in result.keys() and result["expire"]:
            premium = True
            valid_untill = time.mktime(
                datetime.datetime.fromtimestamp(int(result["expire"])).timetuple()
            )

        traffic_left = result["balance"]

        return {
            "validuntil": valid_untill,
            "trafficleft": traffic_left,
            "premium": premium,
        }

    def signin(self, user, password, data):
        data["usr"] = user
        data["pwd"] = hashlib.md5(password.encode()).hexdigest()

        try:
            response = json.loads(self.run_auth_query())

        except Exception:
            self.fail_login()

        if "errno" in response.keys():
            self.fail_login()

    def create_auth_query(self):
        query = self.API_QUERY
        query["username"] = self.info["data"]["usr"]
        query["password"] = self.info["data"]["pwd"]
        return query

    def run_auth_query(self):
        return self.load(self.API_URL, post=self.create_auth_query())
