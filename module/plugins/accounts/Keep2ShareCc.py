# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account
from module.plugins.internal.Plugin import set_cookie


class Keep2ShareCc(Account):
    __name__    = "Keep2ShareCc"
    __type__    = "account"
    __version__ = "0.08"
    __status__  = "testing"

    __description__ = """Keep2Share.cc account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("aeronaut", "aeronaut@pianoguy.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    VALID_UNTIL_PATTERN  = r'Premium expires:\s*<b>(.+?)<'
    TRAFFIC_LEFT_PATTERN = r'Available traffic \(today\):\s*<b><a href="/user/statistic.html">(.+?)<'

    LOGIN_FAIL_PATTERN = r'Please fix the following input errors'


    def parse_info(self, user, password, data, req):
        validuntil  = None
        trafficleft = -1
        premium     = False

        html = self.load("http://keep2share.cc/site/profile.html")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.log_debug("Expire date: " + expiredate)

            if expiredate == "LifeTime":
                premium    = True
                validuntil = -1
            else:
                try:
                    validuntil = time.mktime(time.strptime(expiredate, "%Y.%m.%d"))

                except Exception, e:
                    self.log_error(e)

                else:
                    premium = True if validuntil > time.mktime(time.gmtime()) else False

            m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
            if m:
                try:
                    trafficleft = self.parse_traffic(m.group(1))

                except Exception, e:
                    self.log_error(e)

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, password, data, req):
        set_cookie(req.cj, "keep2share.cc", "lang", "en")

        html = self.load("https://keep2share.cc/login.html",
                         post={'LoginForm[username]'  : user,
                               'LoginForm[password]'  : password,
                               'LoginForm[rememberMe]': 1,
                               'yt0'                  : ""})

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.login_fail()
