# -*- coding: utf-8 -*-

import re

from time import mktime, strptime

from pyload.plugin.Account import Account


class CatShareNet(Account):
    __name    = "CatShareNet"
    __type    = "account"
    __version = "0.05"

    __description = """CatShareNet account plugin"""
    __license     = "GPLv3"
    __authors     = [("prOq", "")]


    PREMIUM_PATTERN      = r'<a href="/premium">Konto:[\s\n]*Premium'
    VALID_UNTIL_PATTERN  = r'>Konto premium.*?<strong>(.*?)</strong></span>'
    TRAFFIC_LEFT_PATTERN = r'<a href="/premium">([0-9.]+ [kMG]B)'


    def loadAccountInfo(self, user, req):
        premium     = False
        validuntil  = -1
        trafficleft = -1

        html = req.load("http://catshare.net/", decode=True)

        if re.search(self.PREMIUM_PATTERN, html):
            premium = True

        try:
            expiredate = re.search(self.VALID_UNTIL_PATTERN, html).group(1)
            self.logDebug("Expire date: " + expiredate)

            validuntil = mktime(strptime(expiredate, "%Y-%m-%d %H:%M:%S"))

        except Exception:
            pass

        try:
            trafficleft = self.parseTraffic(re.search(self.TRAFFIC_LEFT_PATTERN, html).group(1))

        except Exception:
            pass

        return {'premium': premium, 'trafficleft': trafficleft, 'validuntil': validuntil}


    def login(self, user, data, req):
        html = req.load("http://catshare.net/login",
                        post={'user_email': user,
                              'user_password': data['password'],
                              'remindPassword': 0,
                              'user[submit]': "Login"},
                        decode=True)

        if not '<a href="/logout">Wyloguj</a>' in html:
            self.wrongPassword()
