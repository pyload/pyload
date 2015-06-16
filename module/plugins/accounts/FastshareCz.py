# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Account import Account


class FastshareCz(Account):
    __name__    = "FastshareCz"
    __type__    = "account"
    __version__ = "0.07"

    __description__ = """Fastshare.cz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CREDIT_PATTERN = r'Credit\s*:\s*</td>\s*<td>(.+?)\s*<'


    def loadAccountInfo(self, user, req):
        validuntil  = -1
        trafficleft = None
        premium     = False

        html = self.load("http://www.fastshare.cz/user", req=req)

        m = re.search(self.CREDIT_PATTERN, html)
        if m:
            trafficleft = self.parseTraffic(m.group(1))

        premium = bool(trafficleft)

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, data, req):
        req.cj.setCookie("fastshare.cz", "lang", "en")

        self.load('http://www.fastshare.cz/login', req=req)  # Do not remove or it will not login

        html = self.load("https://www.fastshare.cz/sql.php",
                        post={'login': user, 'heslo': data['password']}, req=req)

        if ">Wrong username or password" in html:
            self.wrongPassword()
