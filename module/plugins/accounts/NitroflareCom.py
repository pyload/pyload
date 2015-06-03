# -*- coding: utf-8 -*-

import re
import time

from module.plugins.Account import Account


class NitroflareCom(Account):
    __name__    = "NitroflareCom"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """Nitroflare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"  )]


    VALID_UNTIL_PATTERN = r'>Time Left</label.*>(.+?)</'
    LOGIN_FAIL_PATTERN  = r'<ul class="errors">\s*<li>'


    def loadAccountInfo(self, user, req):
        validuntil   = -1
        trafficleft  = None  #@TODO: Implement traffic left check
        premium      = False

        html = req.load("https://nitroflare.com/member",
                        get={'s': "premium"},
                        decode=True)

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()

            try:
                validuntil = sum(int(v) * {'day': 24 * 3600, 'hour': 3600, 'minute': 60}[u.lower()] for v, u in
                                 re.findall(r'(\d+)\s*(day|hour|minute)', expiredate, re.I))
            except Exception, e:
                self.logError(e)

            else:
                if validuntil:
                    validuntil += time.time()
                    premium = True
                else:
                    validuntil = -1

        return {'validuntil'  : validuntil,
                'trafficleft' : trafficleft,
                'premium'     : premium}


    def login(self, user, data, req):
        html = req.load("https://nitroflare.com/login", decode=True)
        html = req.load("https://nitroflare.com/login",
                        post={'email'   : user,
                              'password': data['password'],
                              'token'   : re.search(r'name="token" value="(.+?)"', html).group(1)},
                        decode=True)

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.wrongPassword()
