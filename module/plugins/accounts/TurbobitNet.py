# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class TurbobitNet(Account):
    __name__    = "TurbobitNet"
    __type__    = "account"
    __version__ = "0.03"

    __description__ = """TurbobitNet account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def loadAccountInfo(self, user, req):
        html = req.load("http://turbobit.net")

        m = re.search(r'<u>Turbo Access</u> to ([\d.]+)', html)
        if m:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y"))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}


    def login(self, user, data, req):
        req.cj.setCookie("turbobit.net", "user_lang", "en")

        html = req.load("http://turbobit.net/user/login",
                        post={"user[login]": user,
                              "user[pass]": data['password'],
                              "user[submit]": "Login"},
                        decode=True)

        if not '<div class="menu-item user-name">' in html:
            self.wrongPassword()
