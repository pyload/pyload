# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class NitroflareCom(Account):
    __name__    = "NitroflareCom"
    __type__    = "account"
    __version__ = "0.06"
    __status__  = "testing"

    __description__ = """Nitroflare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"  )]


    VALID_UNTIL_PATTERN  = r'>Time Left</label><strong>(.+?)</'
    TRAFFIC_LEFT_PATTERN = r'>Daily Limit</label><strong>([\d.,]+)'
    LOGIN_FAIL_PATTERN   = r'<ul class="errors">\s*<li>'

    TOKEN_PATTERN = r'name="token" value="(.+?)"'


    def parse_info(self, user, password, data, req):
        validuntil   = -1
        trafficleft  = None
        premium      = False

        html = self.load("https://nitroflare.com/member",
                         get={'s': "premium"})

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.log_debug("Time Left: " + expiredate)

            try:
                validuntil = sum(int(v) * {'day': 24 * 3600, 'hour': 3600, 'minute': 60}[u.lower()] for v, u in
                                 re.findall(r'(\d+)\s*(day|hour|minute)', expiredate, re.I))
            except Exception, e:
                self.log_error(e)

            else:
                self.log_debug("Valid until: %s" % validuntil)

                if validuntil:
                    validuntil += time.time()
                    premium = True
                else:
                    validuntil = -1

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            try:
                trafficleft = self.parse_traffic(str(max(0, 50 - float(m.group(1)))) + " GB")

            except Exception, e:
                self.log_error(e)
        else:
            self.log_debug("TRAFFIC_LEFT_PATTERN not found")

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, password, data, req):
        html = self.load("https://nitroflare.com/login")

        token = re.search(self.TOKEN_PATTERN, html).group(1)

        html = self.load("https://nitroflare.com/login",
                         post={'login'   : "",
                               'email'   : user,
                               'password': password,
                               'token'   : token})

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.login_fail()
