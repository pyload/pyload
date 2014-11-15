# -*- coding: utf-8 -*-

import re

from time import gmtime, mktime, strptime

from pyload.plugins.internal.Account import Account


class Keep2shareCc(Account):
    __name__    = "Keep2shareCc"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """Keep2share.cc account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("aeronaut", "aeronaut@pianoguy.de")]


    VALID_UNTIL_PATTERN  = r'Premium expires: <b>(.+?)</b>'
    TRAFFIC_LEFT_PATTERN = r'Available traffic \(today\):<b><a href="/user/statistic.html">(.+?)</a>'

    LOGIN_FAIL_PATTERN = r'Please fix the following input errors'


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = None

        html = req.load("http://keep2share.cc/site/profile.html", decode=True)

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = mktime(strptime(expiredate, "%Y.%m.%d"))

            except Exception, e:
                self.logError(e)

            else:
                if validuntil > mktime(gmtime()):
                    premium = True
                else:
                    premium = False
                    validuntil = None

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            try:
                trafficleft = self.parseTraffic(m.group(1))

            except Exception, e:
                self.logError(e)

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, data, req):
        req.cj.setCookie(".keep2share.cc", "lang", "en")

        html = req.load("http://keep2share.cc/login.html",
                        post={'LoginForm[username]': user, 'LoginForm[password]': data['password']})

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.wrongPassword()
