# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class EuroshareEu(Account):
    __name__    = "EuroshareEu"
    __type__    = "account"
    __version__ = "0.03"

    __description__ = """Euroshare.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def loadAccountInfo(self, user, req):
        self.relogin(user)
        html = self.load("http://euroshare.eu/customer-zone/settings/", req=req)

        m = re.search('id="input_expire_date" value="(\d+\.\d+\.\d+ \d+:\d+)"', html)
        if m is None:
            premium    = False
            validuntil = -1
        else:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y %H:%M"))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}


    def login(self, user, data, req):
        html = self.load('http://euroshare.eu/customer-zone/login/',
                        post={"trvale": "1",
                              "login": user,
                              "password": data['password']}, req=req)

        if u">Nesprávne prihlasovacie meno alebo heslo" in html:
            self.wrongPassword()
