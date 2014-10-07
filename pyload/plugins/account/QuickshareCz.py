# -*- coding: utf-8 -*-

import re
from pyload.plugins.base.Account import Account
from pyload.utils import parseFileSize


class QuickshareCz(Account):
    __name__ = "QuickshareCz"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Quickshare.cz account plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.quickshare.cz/premium", decode=True)

        m = re.search(r'Stav kreditu: <strong>(.+?)</strong>', html)
        if m:
            trafficleft = parseFileSize(m.group(1)) / 1024
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
