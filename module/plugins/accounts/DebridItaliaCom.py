# -*- coding: utf-8 -*-

import re

from time import mktime, strptime

from module.plugins.Account import Account


class DebridItaliaCom(Account):
    __name__    = "DebridItaliaCom"
    __type__    = "account"
    __version__ = "0.13"

    __description__ = """Debriditalia.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    WALID_UNTIL_PATTERN = r'Premium valid till: (.+?) \|'


    def loadAccountInfo(self, user, req):
        info = {"premium": False, "validuntil": None, "trafficleft": None}
        html = req.load("http://debriditalia.com/")

        if 'Account premium not activated' not in html:
            m = re.search(self.WALID_UNTIL_PATTERN, html)
            if m:
                validuntil = mktime(strptime(m.group(1), "%d/%m/%Y %H:%M"))
                info = {"premium": True, "validuntil": validuntil, "trafficleft": -1}
            else:
                self.logError(_("Unable to retrieve account information"))

        return info


    def login(self, user, data, req):
        html = req.load("http://debriditalia.com/login.php",
                        get={'u': user, 'p': data['password']},
                        decode=True)

        if 'NO' in html:
            self.wrongPassword()
