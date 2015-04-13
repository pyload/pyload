# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class CzshareCom(Account):
    __name    = "CzshareCom"
    __type    = "account"
    __version = "0.18"

    __description = """Czshare.com account plugin, now Sdilej.cz"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CREDIT_LEFT_PATTERN = r'<tr class="active">\s*<td>([\d ,]+) (KiB|MiB|GiB)</td>\s*<td>([^<]*)</td>\s*</tr>'


    def loadAccountInfo(self, user, req):
        premium     = False
        validuntil  = None
        trafficleft = None

        html = req.load("http://sdilej.cz/prehled_kreditu/")

        try:
            m = re.search(self.CREDIT_LEFT_PATTERN, html)
            trafficleft = self.parseTraffic(m.group(1).replace(' ', '').replace(',', '.')) + m.group(2)
            validuntil  = time.mktime(time.strptime(m.group(3), '%d.%m.%y %H:%M'))

        except Exception, e:
            self.logError(e)

        else:
            premium = True

        return {'premium'    : premium,
                'validuntil' : validuntil,
                'trafficleft': trafficleft}


    def login(self, user, data, req):
        html = req.load('https://sdilej.cz/index.php',
                        post={"Prihlasit": "Prihlasit",
                              "login-password": data['password'],
                              "login-name": user},
                        decode=True)

        if '<div class="login' in html:
            self.wrongPassword()
