# -*- coding: utf-8 -*-

import hashlib
import json
import time

from ..base.multi_account import MultiAccount


class SmoozedCom(MultiAccount):
    __name__ = "SmoozedCom"
    __type__ = "account"
    __version__ = "0.13"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Smoozed.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    def grab_hosters(self, user, password, data):
        return self.get_data("hosters")

    def grab_info(self, user, password, data):
        status = self.get_account_status(user, password)

        self.log_debug(status)

        if status["state"] != "ok":
            info = {"validuntil": None, "trafficleft": None, "premium": False}
        else:
            #: Parse account info
            info = {
                "validuntil": float(status["data"]["user"]["user_premium"]),
                "trafficleft": max(
                    0, status["data"]["traffic"][1] - status["data"]["traffic"][0]
                ),
                "session": status["data"]["session_key"],
                "hosters": [hoster["name"] for hoster in status["data"]["hoster"]],
            }

            if info["validuntil"] < time.time():
                if float(status["data"]["user"].get("user_trial", 0)) > time.time():
                    info["premium"] = True
                else:
                    info["premium"] = False
            else:
                info["premium"] = True

        return info

    def signin(self, user, password, data):
        #: Get user data from premiumize.me
        status = self.get_account_status(user, password)

        #: Check if user and password are valid
        if status["state"] != "ok":
            self.fail_login()

    def get_account_status(self, user, password):
        b_password = password.encode()
        encrypted = hashlib.pbkdf2_hmac("sha256", b_password, b_password, 1000).hex()[
            32
        ]

        html = self.load(
            "http://www2.smoozed.com/api/login",
            get={"auth": user, "password": encrypted},
        )
        return json.loads(html)
