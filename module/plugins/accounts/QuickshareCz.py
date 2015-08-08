# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Account import Account


class QuickshareCz(Account):
    __name__    = "QuickshareCz"
    __type__    = "account"
    __version__ = "0.05"
    __status__  = "testing"

    __description__ = """Quickshare.cz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    TRAFFIC_LEFT_PATTERN = r'Stav kreditu: <strong>(.+?)</strong>'


    def parse_info(self, user, password, data, req):
        html = self.load("http://www.quickshare.cz/premium")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = self.parse_traffic(m.group(1))
            premium = True if trafficleft else False
        else:
            trafficleft = None
            premium = False

        return {'validuntil': -1, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, password, data, req):
        html = self.load('http://www.quickshare.cz/html/prihlaseni_process.php',
                         post={'akce' : u'Přihlásit',
                               'heslo': password,
                               'jmeno': user})

        if u'>Takový uživatel neexistuje.<' in html or u'>Špatné heslo.<' in html:
            self.login_fail()
