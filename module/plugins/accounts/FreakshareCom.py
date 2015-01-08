# -*- coding: utf-8 -*-

import re

from time import strptime, mktime

from module.plugins.Account import Account


class FreakshareCom(Account):
    __name__    = "FreakshareCom"
    __type__    = "account"
    __version__ = "0.13"

    __description__ = """Freakshare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def loadAccountInfo(self, user, req):
        premium = False
        validuntil  = None
        trafficleft = None

        html = req.load("http://freakshare.com/")

        try:
            m = re.search(r'ltig bis:</td>\s*<td><b>([\d.:-]+)</b></td>', html, re.M)
            validuntil = mktime(strptime(m.group(1).strip(), "%d.%m.%Y - %H:%M"))

        except Exception:
            pass

        try:
            m = re.search(r'Traffic verbleibend:</td>\s*<td>([^<]+)', html, re.M)
            trafficleft = self.parseTraffic(m.group(1))

        except Exception:
            pass

        return {"premium": premium, "validuntil": validuntil, "trafficleft": trafficleft}


    def login(self, user, data, req):
        req.load("http://freakshare.com/index.php?language=EN")

        html = req.load("http://freakshare.com/login.html",
                        post={"submit": "Login", "user": user, "pass": data['password']},
                        cookies=True,
                        decode=True)

        if ">Wrong Username or Password" in html:
            self.wrongPassword()
