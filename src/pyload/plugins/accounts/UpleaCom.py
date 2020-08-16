# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class UpleaCom(BaseAccount):
    __name__ = "UpleaCom"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = """UpleaCom account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_URL = r"http://uplea.com"
    LOGIN_SKIP_PATTERN = r'>DISCONNECT</span> <span class="agbold">ME NOW<'

    PREMIUM_PATTERN = r"Uplea premium member <"
    VALID_UNTIL_PATTERN = r"You\'re premium member until .+?>([\d/]+)"

    def grab_info(self, user, password, data):
        trafficleft = -1

        html = self.load("http://uplea.com/account")

        if re.search(self.PREMIUM_PATTERN, html):
            premium = True

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is None:
            premium = False
            validuntil = -1
        else:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d/%m/%Y"))

        return {
            "premium": premium,
            "trafficleft": trafficleft,
            "validuntil": validuntil,
        }

    def signin(self, user, password, data):
        html = self.load("http://uplea.com")

        if self.LOGIN_SKIP_PATTERN in html:
            self.skip_login()

        html = self.load(
            "http://uplea.com",
            post={"login": user, "password": password, "remember": 0, "login-form": ""},
        )

        if self.LOGIN_SKIP_PATTERN not in html:
            self.fail_login()
