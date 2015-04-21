# -*- coding: utf-8 -*-

import re

from pyload.plugin.Account import Account
from pyload.utils import parseFileSize


class FastshareCz(Account):
    __name    = "FastshareCz"
    __type    = "account"
    __version = "0.06"

    __description = """Fastshare.cz account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CREDIT_PATTERN = r'Credit\s*:\s*</td>\s*<td>(.+?)\s*<'


    def loadAccountInfo(self, user, req):
        validuntil  = -1
        trafficleft = None
        premium     = False

        html = req.load("http://www.fastshare.cz/user", decode=True)

        m = re.search(self.CREDIT_PATTERN, html)
        if m:
            trafficleft = self.parseTraffic(m.group(1))

        premium = bool(trafficleft)

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, data, req):
        req.cj.setCookie("fastshare.cz", "lang", "en")

        req.load('http://www.fastshare.cz/login')  #: Do not remove or it will not login

        html = req.load("http://www.fastshare.cz/sql.php",
                        post={'login': user, 'heslo': data['password']},
                        decode=True)

        if ">Wrong username or password" in html:
            self.wrongPassword()
