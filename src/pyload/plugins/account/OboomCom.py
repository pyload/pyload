# -*- coding: utf-8 -*-

import json
from builtins import _

from beaker.crypto.pbkdf2 import PBKDF2

from ..internal.account import Account


class OboomCom(Account):
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
        pbkdf2 = PBKDF2(password, salt, 1000).hexread(16)

        html = self.load(
            "http://www.oboom.com/1/login",  # TODO: Revert to `https` in 0.6.x
            get={"auth": user, "pass": pbkdf2},
        )
        result = json.loads(html)

        if result[0] != 200:
            self.log_warning(self._("Failed to log in: {}").format(result[1]))
            self.fail_login()

        return result[1]

    def grab_info(self, user, password, data):
        account_data = self.load_account_data(user, password)

        userData = account_data["user"]

        premium = userData["premium"] != "null"

        if userData["premium_unix"] == "null":
            validUntil = -1
        else:
            validUntil = float(userData["premium_unix"])

        traffic = userData["traffic"]

        # TODO: Remove `>> 10` in 0.6.x
        trafficLeft = traffic["current"] >> 10
        maxTraffic = traffic["max"] >> 10  # TODO: Remove `>> 10` in 0.6.x

        session = account_data["session"]

        return {
            "premium": premium,
            "validuntil": validUntil,
            "trafficleft": trafficLeft,
            "maxtraffic": maxTraffic,
            "session": session,
        }

    def signin(self, user, password, data):
        self.load_account_data(user, password)
