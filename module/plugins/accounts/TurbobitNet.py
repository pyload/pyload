# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account
from module.plugins.internal.misc import set_cookie


class TurbobitNet(Account):
    __name__    = "TurbobitNet"
    __type__    = "account"
    __version__ = "0.09"
    __status__  = "testing"

    __description__ = """TurbobitNet account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def grab_info(self, user, password, data):
        html = self.load("http://turbobit.net")

        m = re.search(r'<u>Turbo Access</u> to ([\d.]+)', html)
        if m is not None:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y"))
        else:
            premium = False
            validuntil = -1

        return {'premium': premium, 'trafficleft': -1, 'validuntil': validuntil}


    def signin(self, user, password, data):
        set_cookie(self.req.cj, "turbobit.net", "user_lang", "en")

        html = self.load("http://turbobit.net/user/login",
                         post={"user[login]" : user,
                               "user[pass]"  : password,
                               "user[submit]": "Login"})

        if not '<div class="menu-item user-name">' in html:
            self.fail_login()
