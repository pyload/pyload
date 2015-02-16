# -*- coding: utf-8 -*-

import re

from pyload.plugin.Account import Account
from pyload.utils import parseFileSize


class FastshareCz(Account):
    __name    = "FastshareCz"
    __type    = "account"
    __version = "0.05"

    __description = """Fastshare.cz account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CREDIT_PATTERN = r'My account\s*\((.+?)\)'


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = None

        html = req.load("http://www.fastshare.cz/user", decode=True)

        m = re.search(self.CREDIT_PATTERN, html)
        if m:
            trafficleft = self.parseTraffic(m.group(1))

        if trafficleft:
            premium = True
            validuntil = -1
        else:
            premium = False

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}


    def login(self, user, data, req):
        req.cj.setCookie("fastshare.cz", "lang", "en")

        req.load('http://www.fastshare.cz/login')  # Do not remove or it will not login

        html = req.load("http://www.fastshare.cz/sql.php",
                        post={'login': user, 'heslo': data['password']},
                        decode=True)

        if ">Wrong username or password" in html:
            self.wrongPassword()
