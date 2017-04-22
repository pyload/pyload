# -*- coding: utf-8 -*-

import re
import time

from ..internal.Account import Account


class CatShareNet(Account):
    __name__ = "CatShareNet"
    __type__ = "account"
    __version__ = "0.16"
    __status__ = "testing"

    __description__ = """Catshare.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("prOq", None),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PREMIUM_PATTERN = r'<span class="hidden-xs">Premium</span>'
    VALID_UNTIL_PATTERN = r'<span class="hidden-xs">Premium</span> <b>(.*?)</b>'
    TRAFFIC_LEFT_PATTERN = r'<span class="hidden-xs">Premium</span>.*?\( (-?)(?P<S>[\d.,]+) (?P<U>[kMG]B) \)'

    def grab_info(self, user, password, data):
        premium = False
        validuntil = -1
        trafficleft = -1

        html = self.load("http://catshare.net/")

        if re.search(self.PREMIUM_PATTERN, html):
            premium = True

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            m = re.findall(r'(\d+) (tydzień|dni|godzin)', m.group(1))
            if m is not None:
                validuntil = time.time()
                for n, u in m:
                    validuntil += float(n) * 60 * 60 * \
                        {'tydzień': 168, 'dni': 24, 'godzin': 1}[u]

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            trafficleft = 0 if m.group(
                1) else self.parse_traffic(m.group(2), m.group(3))

        return {'premium': premium, 'trafficleft': trafficleft,
                'validuntil': validuntil}

    def signin(self, user, password, data):
        html = self.load("http://catshare.net/")

        if re.search(r'/logout".*>Wyloguj</a>', html) is not None:
            self.skip_login()

        html = self.load("http://catshare.net/login",  # @TODO: Revert to `https` in 0.4.10
                         post={'user_email': user,
                               'user_password': password},
                         redirect=20)

        if re.search(r'/logout".*>Wyloguj</a>', html) is None:
            self.fail_login()
