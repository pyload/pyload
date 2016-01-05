# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class CzshareCom(Account):
    __name__    = "CzshareCom"
    __type__    = "account"
    __version__ = "0.26"
    __status__  = "testing"

    __description__ = """Czshare.com account plugin, now Sdilej.cz"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CREDIT_LEFT_PATTERN = r'<tr class="active">\s*<td>([\d ,]+) (KiB|MiB|GiB)</td>\s*<td>(.*?)</td>\s*</tr>'


    def grab_info(self, user, password, data):
        premium     = False
        validuntil  = None
        trafficleft = None

        html = self.load("http://sdilej.cz/prehled_kreditu/")

        try:
            m = re.search(self.CREDIT_LEFT_PATTERN, html)
            trafficleft = self.parse_traffic(m.group(1), m.group(2))
            validuntil  = time.mktime(time.strptime(m.group(3), '%d.%m.%y %H:%M'))

        except Exception, e:
            self.log_error(e, trace=True)

        else:
            premium = True

        return {'premium'    : premium,
                'validuntil' : validuntil,
                'trafficleft': trafficleft}


    def signin(self, user, password, data):
        html = self.load('https://sdilej.cz/index.php',
                         post={'Prihlasit'     : "Prihlasit",
                               "login-password": password,
                               "login-name"    : user})

        if '<div class="login' in html:
            self.fail_login()
