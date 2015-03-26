# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class DebridItaliaCom(Account):
    __name    = "DebridItaliaCom"
    __type    = "account"
    __version = "0.13"

    __description = """Debriditalia.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    WALID_UNTIL_PATTERN = r'Premium valid till: (.+?) \|'


    def loadAccountInfo(self, user, req):
        info = {'premium': False, 'validuntil': None, 'trafficleft': None}
        html = req.load("http://debriditalia.com/")

        if 'Account premium not activated' not in html:
            m = re.search(self.WALID_UNTIL_PATTERN, html)
            if m:
                validuntil = time.mktime(time.strptime(m.group(1), "%d/%m/%Y %H:%M"))
                info = {'premium': True, 'validuntil': validuntil, 'trafficleft': -1}
            else:
                self.logError(_("Unable to retrieve account information"))

        return info


    def login(self, user, data, req):
        html = req.load("http://debriditalia.com/login.php",
                        get={'u': user, 'p': data['password']},
                        decode=True)

        if 'NO' in html:
            self.wrongPassword()
