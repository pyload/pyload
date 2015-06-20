# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class NitroflareCom(Account):
    __name__    = "NitroflareCom"
    __type__    = "account"
    __version__ = "0.05"

    __description__ = """Nitroflare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"  )]


    VALID_UNTIL_PATTERN  = r'>Time Left</label><strong>(.+?)</'
    TRAFFIC_LEFT_PATTERN = r'>Daily Limit</label><strong>([\d.,]+)'
    LOGIN_FAIL_PATTERN   = r'<ul class="errors">\s*<li>'

    TOKEN_PATTERN = r'name="token" value="(.+?)"'


    def loadAccountInfo(self, user, req):
        validuntil   = -1
        trafficleft  = None
        premium      = False

        html = req.load("https://nitroflare.com/member",
                        get={'s': "premium"},
                        decode=True)

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.logDebug("Time Left: " + expiredate)

            try:
                validuntil = sum(int(v) * {'day': 24 * 3600, 'hour': 3600, 'minute': 60}[u.lower()] for v, u in
                                 re.findall(r'(\d+)\s*(day|hour|minute)', expiredate, re.I))
            except Exception, e:
                self.logError(e)

            else:
                self.logDebug("Valid until: %s" % validuntil)

                if validuntil:
                    validuntil += time.time()
                    premium = True
                else:
                    validuntil = -1

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            try:
                trafficleft = self.parseTraffic(str(max(0, 50 - float(m.group(1)))) + " GB")

            except Exception, e:
                self.logError(e)
        else:
            self.logDebug("TRAFFIC_LEFT_PATTERN not found")

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, data, req):
        html = req.load("https://nitroflare.com/login", decode=True)

        token = re.search(self.TOKEN_PATTERN, html).group(1)

        html = req.load("https://nitroflare.com/login",
                        post={'login'   : "",
                              'email'   : user,
                              'password': data['password'],
                              'token'   : token},
                        decode=True)

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.wrongPassword()
