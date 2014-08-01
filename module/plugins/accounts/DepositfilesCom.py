# -*- coding: utf-8 -*-

import re

from time import strptime, mktime

from module.plugins.Account import Account


class DepositfilesCom(Account):
    __name__ = "DepositfilesCom"
    __type__ = "account"
    __version__ = "0.3"

    __description__ = """Depositfiles.com account plugin"""
    __author_name__ = ("mkaay", "stickell", "Walter Purcaro")
    __author_mail__ = ("mkaay@mkaay.de", "l.stickell@yahoo.it", "vuolter@gmail.com")


    def loadAccountInfo(self, user, req):
        src = req.load("https://dfiles.eu/de/gold/")
        validuntil = re.search(r"Sie haben Gold Zugang bis: <b>(.*?)</b></div>", src).group(1)

        validuntil = int(mktime(strptime(validuntil, "%Y-%m-%d %H:%M:%S")))

        return {"validuntil": validuntil, "trafficleft": -1}

    def login(self, user, data, req):
        src = req.load("https://dfiles.eu/de/login.php", get={"return": "/de/gold/payment.php"},
                       post={"login": user, "password": data['password']})
        if r'<div class="error_message">Sie haben eine falsche Benutzername-Passwort-Kombination verwendet.</div>' in src:
            self.wrongPassword()
