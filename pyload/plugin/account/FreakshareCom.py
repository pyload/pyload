# -*- coding: utf-8 -*-

import re

from time import strptime, mktime

from pyload.plugin.Account import Account


class FreakshareCom(Account):
    __name    = "FreakshareCom"
    __type    = "account"
    __version = "0.11"

    __description = """Freakshare.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


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
