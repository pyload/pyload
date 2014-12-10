# -*- coding: utf-8 -*-

import re

from pyload.plugins.Account import Account


class QuickshareCz(Account):
    __name    = "QuickshareCz"
    __type    = "account"
    __version = "0.02"

    __description = """Quickshare.cz account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    TRAFFIC_LEFT_PATTERN = r'Stav kreditu: <strong>(.+?)</strong>'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.quickshare.cz/premium", decode=True)

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = self.parseTraffic(m.group(1))
            premium = True if trafficleft else False
        else:
            trafficleft = None
            premium = False

        return {"validuntil": -1, "trafficleft": trafficleft, "premium": premium}


    def login(self, user, data, req):
        html = req.load('http://www.quickshare.cz/html/prihlaseni_process.php', post={
            "akce": u'Přihlásit',
            "heslo": data['password'],
            "jmeno": user
        }, decode=True)

        if u'>Takový uživatel neexistuje.<' in html or u'>Špatné heslo.<' in html:
            self.wrongPassword()
