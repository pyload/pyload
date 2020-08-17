# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class FreakshareCom(BaseAccount):
    __name__ = "FreakshareCom"
    __type__ = "account"
    __version__ = "0.21"
    __status__ = "testing"

    __description__ = """Freakshare.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net")]

    def grab_info(self, user, password, data):
        premium = False
        validuntil = None
        trafficleft = None

        html = self.load("http://freakshare.com/")

        try:
            m = re.search(r"ltig bis:</td>\s*<td><b>([\d.:\-]+)</b></td>", html, re.M)
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y - %H:%M"))

        except Exception:
            pass

        try:
            m = re.search(r"Traffic verbleibend:</td>\s*<td>(.+?)", html, re.M)
            trafficleft = self.parse_traffic(m.group(1))

        except Exception:
            pass

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        self.load("http://freakshare.com/index.php?language=EN")

        html = self.load(
            "https://freakshare.com/login.html",
            post={"submit": "Login", "user": user, "pass": password},
        )

        if ">Wrong Username or Password" in html:
            self.fail_login()
