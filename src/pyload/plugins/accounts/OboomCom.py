# -*- coding: utf-8 -*-

import json
import hashlib

from ..base.account import BaseAccount


class OboomCom(BaseAccount):
    __name__ = "OboomCom"
    __type__ = "account"
    __version__ = "0.32"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __description__ = """Oboom.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stanley", "stanley.foerster@gmail.com")]

    def load_account_data(self, user, password):
        salt = password[::-1]
        pw = hashlib.pbkdf2_hmac(password.encode(), salt.encode(), 1000).hex()[16]

        html = self.load(
            "http://www.oboom.com/1/login",  # TODO: Revert to `https` in 0.6.x
            get={"auth": user, "pass": pw},
        )
        result = json.loads(html)

        if result[0] != 200:
            self.log_warning(self._("Failed to log in: {}").format(result[1]))
            self.fail_login()

        return result[1]

    def grab_info(self, user, password, data):
        account_data = self.load_account_data(user, password)

        user_data = account_data["user"]

        premium = user_data["premium"] != "null"

        if user_data["premium_unix"] == "null":
            valid_until = -1
        else:
            valid_until = float(user_data["premium_unix"])

        traffic = user_data["traffic"]

        # TODO: Remove `>> 10` in 0.6.x
        traffic_left = traffic["current"] >> 10
        max_traffic = traffic["max"] >> 10  # TODO: Remove `>> 10` in 0.6.x

        session = account_data["session"]

        return {
            "premium": premium,
            "validuntil": valid_until,
            "trafficleft": traffic_left,
            "maxtraffic": max_traffic,
            "session": session,
        }

    def signin(self, user, password, data):
        self.load_account_data(user, password)
