# -*- coding: utf-8 -*-

import re
from module.plugins.Account import Account


class FastshareCz(Account):
    __name__    = "FastshareCz"
    __type__    = "account"
    __version__ = "0.04"

    __description__ = """Fastshare.cz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CREDIT_PATTERN = r'(?:Kredit|Credit)\s*</td>\s*<td[^>]*>([\w.]+)&nbsp;'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.fastshare.cz/user", decode=True)

        m = re.search(self.CREDIT_PATTERN, html)
        if m:
            trafficleft = self.parseTraffic(m.group(1))
            premium = True if trafficleft else False
        else:
            trafficleft = None
            premium = False

        return {"validuntil": -1, "trafficleft": trafficleft, "premium": premium}


    def login(self, user, data, req):
        req.load('http://www.fastshare.cz/login')  # Do not remove or it will not login
        html = req.load('http://www.fastshare.cz/sql.php', post={
            "heslo": data['password'],
            "login": user
        }, decode=True)

        if u'>Špatné uživatelské jméno nebo heslo.<' in html:
            self.wrongPassword()
