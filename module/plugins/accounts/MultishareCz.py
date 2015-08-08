# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Account import Account


class MultishareCz(Account):
    __name__    = "MultishareCz"
    __type__    = "account"
    __version__ = "0.07"
    __status__  = "testing"

    __description__ = """Multishare.cz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    TRAFFIC_LEFT_PATTERN = r'<span class="profil-zvyrazneni">Kredit:</span>\s*<strong>(?P<S>[\d.,]+)&nbsp;(?P<U>[\w^_]+)</strong>'
    ACCOUNT_INFO_PATTERN = r'<input type="hidden" id="(u_ID|u_hash)" name=".+?" value="(.+?)">'


    def parse_info(self, user, password, data, req):
        # self.relogin(user)
        html = self.load("http://www.multishare.cz/profil/")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        trafficleft = self.parse_traffic(m.group('S') + m.group('U')) if m else 0
        self.premium = True if trafficleft else False

        html = self.load("http://www.multishare.cz/")
        mms_info = dict(re.findall(self.ACCOUNT_INFO_PATTERN, html))

        return dict(mms_info, **{'validuntil': -1, 'trafficleft': trafficleft})


    def login(self, user, password, data, req):
        html = self.load('https://www.multishare.cz/html/prihlaseni_process.php',
                         post={'akce' : "Přihlásit",
                               'heslo': password,
                               'jmeno': user})

        if '<div class="akce-chyba akce">' in html:
            self.login_fail()
