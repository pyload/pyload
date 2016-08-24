# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class CatShareNet(Account):
    __name__    = "CatShareNet"
    __type__    = "account"
    __version__ = "0.13"
    __status__  = "testing"

    __description__ = """Catshare.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("prOq",      None                        ),
                       ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    PREMIUM_PATTERN      = r'<a href="/premium">Konto:[\s\n]*Premium'
    VALID_UNTIL_PATTERN  = r'>Konto premium.*?<strong>(.*?)</strong></span>'
    TRAFFIC_LEFT_PATTERN = r'<a href="/premium">(?P<S>[\d.,]+) (?P<U>[kMG]B)'


    def grab_info(self, user, password, data):
        premium     = False
        validuntil  = -1
        trafficleft = -1

        html = self.load("http://catshare.net/")

        if re.search(self.PREMIUM_PATTERN, html):
            premium = True

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            validuntil = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = self.parse_traffic(m.group(1), m.group(2))

        return {'premium': premium, 'trafficleft': trafficleft, 'validuntil': validuntil}


    def signin(self, user, password, data):
        html = self.load("http://catshare.net/")

        if '<a href="/logout">Wyloguj</a>' in html:
            self.skip_login()

        html = self.load("http://catshare.net/login",  #@TODO: Revert to `https` in 0.4.10
                         post={'user_email'    : user,
                               'user_password' : password,
                               'remindPassword': 0,
                               'user[submit]'  : "Login"})

        if not '<a href="/logout">Wyloguj</a>' in html:
            self.fail_login()
