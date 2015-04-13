# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class DepositfilesCom(Account):
    __name    = "DepositfilesCom"
    __type    = "account"
    __version = "0.32"

    __description = """Depositfiles.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def loadAccountInfo(self, user, req):
        html = req.load("https://dfiles.eu/de/gold/")
        validuntil = re.search(r"Sie haben Gold Zugang bis: <b>(.*?)</b></div>", html).group(1)

        validuntil = time.mktime(time.strptime(validuntil, "%Y-%m-%d %H:%M:%S"))

        return {"validuntil": validuntil, "trafficleft": -1}


    def login(self, user, data, req):
        html = req.load("https://dfiles.eu/de/login.php", get={"return": "/de/gold/payment.php"},
                        post={"login": user, "password": data['password']},
                        decode=True)

        if r'<div class="error_message">Sie haben eine falsche Benutzername-Passwort-Kombination verwendet.</div>' in html:
            self.wrongPassword()
