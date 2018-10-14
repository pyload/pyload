# -*- coding: utf-8 -*-

from builtins import _

from pyload.plugins.internal.account import Account
from pyload.plugins.utils import json

from beaker.crypto.pbkdf2 import PBKDF2


class OboomCom(Account):
    __name__ = "OboomCom"
    __type__ = "account"
    __version__ = "0.32"
    __pyload_version__ = "0.5"
    __status__ = "testing"

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
            self.log_warning(_("Failed to log in: {}").format(result[1]))
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

        # TODO: Remove `/ 1024` in 0.6.x
        trafficLeft = traffic["current"] // 1024
        maxTraffic = traffic["max"] // 1024  # TODO: Remove `/ 1024` in 0.6.x

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
