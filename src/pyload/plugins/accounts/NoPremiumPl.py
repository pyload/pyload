# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import time

from ..base.multi_account import MultiAccount


class NoPremiumPl(MultiAccount):
    __name__ = "NoPremiumPl"
    __type__ = "account"
    __version__ = "0.11"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = "NoPremium.pl account plugin"
    __license__ = "GPLv3"
    __authors__ = [
        ("goddie", "dev@nopremium.pl"),
        ("GammaC0de", "nitzo2001[AT]yahho[DOT]com"),
    ]

    API_URL = "http://crypt.nopremium.pl"
    API_QUERY = {
        "site": "nopremium",
        "username": "",
        "password": "",
        "output": "json",
        "loc": "1",
        "info": "1",
    }

    def grab_hosters(self, user, password, data):
        html = self.load("https://www.nopremium.pl/clipboard.php?json=3").strip()
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

        valid_untill = -1

        if result.get("expire"):
            valid_untill = time.mktime(
                datetime.datetime.fromtimestamp(int(result["expire"])).timetuple()
            )

        traffic_left = result["balance"] << 10

        return {
            "validuntil": valid_untill,
            "trafficleft": traffic_left,
            "premium": True,
        }

    def signin(self, user, password, data):
        data["hash_password"] = hashlib.sha1(
            hashlib.md5(password.encode()).hexdigest().encode()
        ).hexdigest()

        try:
            response = json.loads(self.run_auth_query())

        except Exception as exc:
            self.fail_login(exc)

        if "errno" in response.keys():
            self.fail_login()

    def create_auth_query(self):
        query = self.API_QUERY
        query["username"] = self.user
        query["password"] = self.info["data"]["hash_password"]
        return query

    def run_auth_query(self):
        return self.load(self.API_URL, post=self.create_auth_query(), redirect=20)
