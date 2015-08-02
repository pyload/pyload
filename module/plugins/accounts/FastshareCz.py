# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Account import Account
from module.plugins.internal.Plugin import set_cookie


class FastshareCz(Account):
    __name__    = "FastshareCz"
    __type__    = "account"
    __version__ = "0.09"
    __status__  = "testing"

    __description__ = """Fastshare.cz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CREDIT_PATTERN = r'Credit\s*:\s*</td>\s*<td>(.+?)\s*<'


    def parse_info(self, user, password, data, req):
        validuntil  = -1
        trafficleft = None
        premium     = False

        html = self.load("http://www.fastshare.cz/user")

        m = re.search(self.CREDIT_PATTERN, html)
        if m:
            trafficleft = self.parse_traffic(m.group(1))

        premium = bool(trafficleft)

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, password, data, req):
        set_cookie(req.cj, "fastshare.cz", "lang", "en")

        self.load('http://www.fastshare.cz/login')  #@NOTE: Do not remove or it will not login

        html = self.load("https://www.fastshare.cz/sql.php",
                         post={'login': user,
                               'heslo': password})

        if ">Wrong username or password" in html:
            self.login_fail()
