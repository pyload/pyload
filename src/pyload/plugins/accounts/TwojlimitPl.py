# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import time

from ..base.multi_account import MultiAccount


class TwojlimitPl(MultiAccount):
    __name__ = "TwojlimitPl"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = "Twojlimit.pl account plugin"
    __license__ = "GPLv3"
    __authors__ = [
        ("synweap15", "pawel@twojlimit.pl"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://crypt.twojlimit.pl"
    API_QUERY = {
        "site": "newtl",
        "username": "",
        "password": "",
        "output": "json",
        "loc": "1",
        "info": "1",
    }

    def grab_hosters(self, user, password, data):
        html = self.load("https://www.twojlimit.pl/clipboard.php", get={"json": "3"})

        json_data = json.loads(html)
        return [
            h for row in json_data for h in row["domains"] if row["sdownload"] == "0"
        ]

    def grab_info(self, user, password, data):
        premium = False
        validuntil = -1
        trafficleft = None

        try:
            json_data = json.loads(self.run_auth_query())

            if json_data.get("expire"):
                premium = True
                validuntil = time.mktime(
                    datetime.datetime.fromtimestamp(
                        int(json_data["expire"])
                    ).timetuple()
                )

            trafficleft = json_data["balance"]

        except Exception as exc:
            self.log_error(exc)

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        data["hash_password"] = hashlib.md5(password.encode()).hexdigest()

        try:
            response = json.loads(self.run_auth_query())

        except Exception as exc:
            self.log_error(exc)
            self.fail_login()

        else:
            if "errno" in response:
                self.fail_login()

    def run_auth_query(self):
        query = self.API_QUERY
        query["username"] = self.user
        query["password"] = self.info["data"]["hash_password"]

        return self.load(self.API_URL, post=query)
