# -*- coding: utf-8 -*-

import re

from ..base.account import BaseAccount


class QuickshareCz(BaseAccount):
    __name__ = "QuickshareCz"
    __type__ = "account"
    __version__ = "0.11"
    __status__ = "testing"

    __description__ = """Quickshare.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    TRAFFIC_LEFT_PATTERN = r"Stav kreditu: <strong>(.+?)</strong>"

    def grab_info(self, user, password, data):
        html = self.load("http://www.quickshare.cz/premium")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            trafficleft = self.parse_traffic(m.group(1))
            premium = True if trafficleft else False
        else:
            trafficleft = None
            premium = False

        return {"validuntil": -1, "trafficleft": trafficleft, "premium": premium}

    def signin(self, user, password, data):
        html = self.load(
            "http://www.quickshare.cz/html/prihlaseni_process.php",
            post={"akce": "Přihlásit", "heslo": password, "jmeno": user},
        )

        if ">Takový uživatel neexistuje.<" in html or ">Špatné heslo.<" in html:
            self.fail_login()
