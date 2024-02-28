# -*- coding: utf-8 -*-

import re
import time

from ..internal.Account import Account
from ..internal.misc import json


class OboomIo(Account):
    __name__ = "OboomIo"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Oboom.io account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PREMIUM_PATTERN = r">Plan <b>Elite</b>"
    VALID_UNTIL_PATTERN = r'fa-calendar-star"></i></div>\s*<p class="d-box-text">([\d\w,\.: ]+)'

    def grab_info(self, user, password, data):
        html = self.load("https://oboom.io/dashboard")

        premium = re.search(self.PREMIUM_PATTERN, html) is not None

        validuntil = None
        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            validuntil = time.mktime(time.strptime(m.group(1).strip(), "%d %b %Y, %H:%M"))

        else:
            self.log_error(self._("VALID_UNTIL_PATTERN not found"))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        html = self.load("https://oboom.io/dashboard")
        if 'href="/logout"' in html:
            self.skip_login()

        html = self.load(
            "https://oboom.io/api/1.0/apiGetUserLogin/",
            post={
                "email": user,
                "pass": password,
                "re": "0"
            }
        )
        json_data = json.loads(html)
        if json_data.get("message") != "successUserLogin":
            self.fail_login()
