# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class TurbobitNet(Account):
    __name__    = "TurbobitNet"
    __type__    = "account"
    __version__ = "0.04"
    __status__  = "testing"

    __description__ = """TurbobitNet account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def load_account_info(self, user, req):
        html = self.load("http://turbobit.net")

        m = re.search(r'<u>Turbo Access</u> to ([\d.]+)', html)
        if m:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y"))
        else:
            premium = False
            validuntil = -1

        return {'premium': premium, 'trafficleft': -1, 'validuntil': validuntil}


    def login(self, user, data, req):
        req.cj.setCookie("turbobit.net", "user_lang", "en")

        html = self.load("http://turbobit.net/user/login",
                         post={"user[login]" : user,
                               "user[pass]"  : data['password'],
                               "user[submit]": "Login"})

        if not '<div class="menu-item user-name">' in html:
            self.wrong_password()
