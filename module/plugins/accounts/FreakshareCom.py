# -*- coding: utf-8 -*-

import re
from time import strptime, mktime

from module.plugins.Account import Account


class FreakshareCom(Account):
    __name__ = "FreakshareCom"
    __type__ = "account"
    __version__ = "0.1"

    __description__ = """Freakshare.com account plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"


    def loadAccountInfo(self, user, req):
        page = req.load("http://freakshare.com/")

        validuntil = r"ltig bis:</td>\s*<td><b>([0-9 \-:.]+)</b></td>"
        validuntil = re.search(validuntil, page, re.MULTILINE)
        validuntil = validuntil.group(1).strip()
        validuntil = mktime(strptime(validuntil, "%d.%m.%Y - %H:%M"))

        traffic = r"Traffic verbleibend:</td>\s*<td>([^<]+)"
        traffic = re.search(traffic, page, re.MULTILINE)
        traffic = traffic.group(1).strip()
        traffic = self.parseTraffic(traffic)

        return {"validuntil": validuntil, "trafficleft": traffic}

    def login(self, user, data, req):
        page = req.load("http://freakshare.com/login.html", None,
                        {"submit": "Login", "user": user, "pass": data['password']}, cookies=True)

        if "Falsche Logindaten!" in page or "Wrong Username or Password!" in page:
            self.wrongPassword()
