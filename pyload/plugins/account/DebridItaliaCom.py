# -*- coding: utf-8 -*-

import re
import time

from pyload.plugins.internal.Account import Account


class DebridItaliaCom(Account):
    __name__    = "DebridItaliaCom"
    __type__    = "account"
    __version__ = "0.1"

    __description__ = """Debriditalia.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    WALID_UNTIL_PATTERN = r'Premium valid till: (?P<D>[^|]+) \|'


    def loadAccountInfo(self, user, req):
        html = req.load("http://debriditalia.com/")

        if 'Account premium not activated' in html:
            return {"premium": False, "validuntil": None, "trafficleft": None}

        m = re.search(self.WALID_UNTIL_PATTERN, html)
        if m:
            validuntil = int(time.mktime(time.strptime(m.group('D'), "%d/%m/%Y %H:%M")))
            return {"premium": True, "validuntil": validuntil, "trafficleft": -1}
        else:
            self.logError(_("Unable to retrieve account information"))


    def login(self, user, data, req):
        html = req.load("http://debriditalia.com/login.php",
                        get={"u": user, "p": data['password']})
        if 'NO' in html:
            self.wrongPassword()
