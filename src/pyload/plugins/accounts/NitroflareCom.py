# -*- coding: utf-8 -*-
import json
import time

from ..base.account import BaseAccount


class NitroflareCom(BaseAccount):
    __name__ = "NitroflareCom"
    __type__ = "account"
    __version__ = "0.20"
    __status__ = "testing"

    __description__ = """Nitroflare.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def grab_info(self, user, password, data):
        validuntil = -1
        trafficleft = None
        premium = False

        data = json.loads(
            self.load(
                "https://nitroflare.com/api/v2/getKeyInfo",
                get={"user": user, "premiumKey": password},
            )
        )

        if data["type"] == "success":
            trafficleft = self.parse_traffic(data["result"]["trafficLeft"], "byte")
            premium = data["result"]["status"] == "active"

            if premium:
                validuntil = time.mktime(
                    time.strptime(data["result"]["expiryDate"], "%Y-%m-%d %H:%M:%S")
                )

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        data = json.loads(
            self.load(
                "https://nitroflare.com/api/v2/getKeyInfo",
                get={"user": user, "premiumKey": password},
            )
        )

        if data["type"] != "success":
            self.fail_login()

        elif data["result"].get("status") == "banned":
            self.fail_login(self._("Banned"))

        elif "recaptchaPublic" in data["result"]:
            self.fail_login(self._("Account Login Requires Recaptcha"))
