# -*- coding: utf-8 -*-

import re
import time

from pyload.core.utils import parse
from ..base.account import BaseAccount
from ..helpers import parse_html_form


class WrzucajplikiPl(BaseAccount):
    __name__ = "WrzucajplikiPl"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Wrzucajpliki.pl account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    TRAFFIC_LEFT_PATTERN = r'<span>Traffic available</span>\s*<div class="price">(?:<sup>(?P<U>[^<>]+)</sup>)?(?P<S>-?\d+)'
    VALID_UNTIL_PATTERN = r">Twoje premium wygaśnie za :</span>\s*</span>\s*<span>(.+?)<"

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = False

        html = self.load("https://wrzucajpliki.pl/account/")
        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            trafficleft = self.parse_traffic(m.group("S"), m.group("U"))

        else:
            self.log_error(self._("TRAFFIC_LEFT_PATTERN not found"))

        now = time.time()
        html = self.load("https://wrzucajpliki.pl/premium/")
        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            validuntil = now + parse.seconds(m.group(1))
            premium = validuntil >= now

        else:
            self.log_error(self._("TRAFFIC_LEFT_PATTERN not found"))

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        html = self.load("https://wrzucajpliki.pl/login/")
        if "https://wrzucajpliki.pl/logout/" in html:
            self.skip_login()

        url, inputs = parse_html_form('name="FL"', html)
        if inputs is None:
            self.fail_login("Login form not found")

        inputs["login"] = user
        inputs["password"] = password

        html = self.load(url, post=inputs)
        if "https://wrzucajpliki.pl/logout/" not in html:
            self.fail_login()
