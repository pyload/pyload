# -*- coding: utf-8 -*-

import re

from time import strptime, mktime

from module.plugins.Account import Account


class FreakshareCom(Account):
    __name__    = "FreakshareCom"
    __type__    = "account"
    __version__ = "0.11"

    __description__ = """Freakshare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def loadAccountInfo(self, user, req):
        page = req.load("http://freakshare.com/")

        validuntil = r'ltig bis:</td>\s*<td><b>([\d.:-]+)</b></td>'
        validuntil = re.search(validuntil, page, re.M)
        validuntil = validuntil.group(1).strip()
        validuntil = mktime(strptime(validuntil, "%d.%m.%Y - %H:%M"))

        traffic = r'Traffic verbleibend:</td>\s*<td>([^<]+)'
        traffic = re.search(traffic, page, re.M)
        traffic = traffic.group(1).strip()
        traffic = self.parseTraffic(traffic)

        return {"validuntil": validuntil, "trafficleft": traffic}


    def login(self, user, data, req):
        req.load("http://freakshare.com/index.php?language=EN")

        page = req.load("http://freakshare.com/login.html", None,
                        {"submit": "Login", "user": user, "pass": data['password']}, cookies=True)

        if ">Wrong Username or Password" in page:
            self.wrongPassword()
