# -*- coding: utf-8 -*-

import re
from time import mktime, strptime

from pyload.plugin.Account import Account


class TurbobitNet(Account):
    __name    = "TurbobitNet"
    __type    = "account"
    __version = "0.02"

    __description = """TurbobitNet account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    def loadAccountInfo(self, user, req):
        html = req.load("http://turbobit.net")

        m = re.search(r'<u>Turbo Access</u> to ([\d.]+)', html)
        if m:
            premium = True
            validuntil = mktime(strptime(m.group(1), "%d.%m.%Y"))
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
