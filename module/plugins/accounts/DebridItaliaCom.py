# -*- coding: utf-8 -*-

import re
import time

from module.plugins.Account import Account


class DebridItaliaCom(Account):
    __name__ = "DebridItaliaCom"
    __type__ = "account"
    __version__ = "0.1"

    __description__ = """Debriditalia.com account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    WALID_UNTIL_PATTERN = r"Premium valid till: (?P<D>[^|]+) \|"


    def loadAccountInfo(self, user, req):
        if 'Account premium not activated' in self.html:
            return {"premium": False, "validuntil": None, "trafficleft": None}

        m = re.search(self.WALID_UNTIL_PATTERN, self.html)
        if m:
            validuntil = int(time.mktime(time.strptime(m.group('D'), "%d/%m/%Y %H:%M")))
            return {"premium": True, "validuntil": validuntil, "trafficleft": -1}
        else:
            self.logError('Unable to retrieve account information - Plugin may be out of date')

    def login(self, user, data, req):
        self.html = req.load("http://debriditalia.com/login.php",
                             get={"u": user, "p": data['password']})
        if 'NO' in self.html:
            self.wrongPassword()
