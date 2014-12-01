# -*- coding: utf-8 -*-

import re

from time import mktime, strptime

from pyload.plugins.internal.Account import Account


class CatShareNet(Account):
    __name__    = "CatShareNet"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """CatShareNet account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("prOq", None)]


    PREMIUM_PATTERN = r'class="nav-collapse collapse pull-right">[\s\w<>=-."/:]*\sz.</a></li>\s*<li><a href="/premium">.*\s*<span style="color: red">(.*?)</span>[\s\w<>/]*href="/logout"'
    VALID_UNTIL_PATTERN = r'<div class="span6 pull-right">[\s\w<>=-":;]*<span style="font-size:13px;">.*?<strong>(.*?)</strong></span>'


    def loadAccountInfo(self, user, req):
        premium = False
        validuntil = -1

        html = req.load("http://catshare.net/", decode=True)

        try:
            m = re.search(self.PREMIUM_PATTERN, html)
            if "Premium" in m.group(1):
                premium = True
        except Exception:
            pass

        try:
            m = re.search(self.VALID_UNTIL_PATTERN, html)
            expiredate = m.group(1)
            if "-" not in expiredate:
                validuntil = mktime(strptime(expiredate, "%d.%m.%Y"))
        except Exception:
            pass

        return {'premium': premium, 'trafficleft': -1, 'validuntil': validuntil}


    def login(self, user, data, req):
        html = req.load("http://catshare.net/login",
                        post={'user_email': user,
                              'user_password': data['password'],
                              'remindPassword': 0,
                              'user[submit]': "Login"})

        if not '<a href="/logout">Wyloguj</a>' in html:
            self.wrongPassword()
