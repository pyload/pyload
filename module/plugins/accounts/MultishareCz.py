# -*- coding: utf-8 -*-

import re

from module.plugins.Account import Account


class MultishareCz(Account):
    __name__    = "MultishareCz"
    __type__    = "account"
    __version__ = "0.05"

    __description__ = """Multishare.cz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    TRAFFIC_LEFT_PATTERN = r'<span class="profil-zvyrazneni">Kredit:</span>\s*<strong>(?P<S>[\d.,]+)&nbsp;(?P<U>[\w^_]+)</strong>'
    ACCOUNT_INFO_PATTERN = r'<input type="hidden" id="(u_ID|u_hash)" name="[^"]*" value="([^"]+)">'


    def loadAccountInfo(self, user, req):
        #self.relogin(user)
        html = req.load("http://www.multishare.cz/profil/", decode=True)

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        trafficleft = self.parseTraffic(m.group('S') + m.group('U')) if m else 0
        self.premium = True if trafficleft else False

        html = req.load("http://www.multishare.cz/", decode=True)
        mms_info = dict(re.findall(self.ACCOUNT_INFO_PATTERN, html))

        return dict(mms_info, **{"validuntil": -1, "trafficleft": trafficleft})


    def login(self, user, data, req):
        html = req.load('http://www.multishare.cz/html/prihlaseni_process.php',
                        post={"akce" : "Přihlásit",
                              "heslo": data['password'],
                              "jmeno": user},
                        decode=True)

        if '<div class="akce-chyba akce">' in html:
            self.wrongPassword()
