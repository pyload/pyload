# -*- coding: utf-8 -*-

import re

from pyload.plugin.Account import Account


class CloudzillaTo(Account):
    __name    = "CloudzillaTo"
    __type    = "account"
    __version = "0.02"

    __description = """Cloudzilla.to account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    PREMIUM_PATTERN = r'<h2>account type</h2>\s*Premium Account'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.cloudzilla.to/")

        premium = re.search(self.PREMIUM_PATTERN, html) is not None

        return {'validuntil': -1, 'trafficleft': -1, 'premium': premium}


    def login(self, user, data, req):
        html = req.load("http://www.cloudzilla.to/",
                        post={'lusername': user,
                              'lpassword': data['password'],
                              'w'        : "dologin"},
                        decode=True)

        if "ERROR" in html:
            self.wrongPassword()
