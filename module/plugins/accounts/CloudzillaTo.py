# -*- coding: utf-8 -*-

import re

from ..internal.Account import Account


class CloudzillaTo(Account):
    __name__ = "CloudzillaTo"
    __type__ = "account"
    __version__ = "0.09"
    __status__ = "testing"

    __description__ = """Cloudzilla.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PREMIUM_PATTERN = r'<h2>account type</h2>\s*Premium Account'

    def grab_info(self, user, password, data):
        html = self.load("http://www.cloudzilla.to/")

        premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        return {'validuntil': -1, 'trafficleft': -1, 'premium': premium}

    def signin(self, user, password, data):
        html = self.load("https://www.cloudzilla.to/",
                         post={'lusername': user,
                               'lpassword': password,
                               'w': "dologin"})

        if "ERROR" in html:
            self.fail_login()
