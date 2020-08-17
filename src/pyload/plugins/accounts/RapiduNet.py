# -*- coding: utf-8 -*-

import json
import re
import time

from ..base.account import BaseAccount


class RapiduNet(BaseAccount):
    __name__ = "RapiduNet"
    __type__ = "account"
    __version__ = "0.12"
    __status__ = "testing"

    __description__ = """Rapidu.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("prOq", None), ("Walter Purcaro", "vuolter@gmail.com")]

    PREMIUM_PATTERN = r">Account: <b>Premium"

    VALID_UNTIL_PATTERN = r">Account: <b>\w+ \((\d+)"

    TRAFFIC_LEFT_PATTERN = r'class="tipsyS"><b>([\d.,]+)\s*([\w^_]*)<'

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = -1
        premium = False

        html = self.load("https://rapidu.net/")

        if re.search(self.PREMIUM_PATTERN, html):
            premium = True

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            validuntil = time.time() + (86400 * int(m.group(1)))

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            trafficleft = self.parse_traffic(m.group(1), m.group(2))

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        self.load(
            "https://rapidu.net/ajax.php",
            get={"a": "getChangeLang"},
            post={"_go": "", "lang": "en"},
        )

        html = self.load(
            "https://rapidu.net/ajax.php",
            get={"a": "getUserLogin"},
            post={"_go": "", "login": user, "pass": password, "remember": "1"},
        )
        json_data = json.loads(html)

        self.log_debug(json_data)

        if json_data["message"] != "success":
            self.fail_login()
