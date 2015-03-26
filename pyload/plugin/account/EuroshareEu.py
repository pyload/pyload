# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class EuroshareEu(Account):
    __name    = "EuroshareEu"
    __type    = "account"
    __version = "0.02"

    __description = """Euroshare.eu account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    def loadAccountInfo(self, user, req):
        self.relogin(user)
        html = req.load("http://euroshare.eu/customer-zone/settings/")

        m = re.search('id="input_expire_date" value="(\d+\.\d+\.\d+ \d+:\d+)"', html)
        if m is None:
            premium, validuntil = False, -1
        else:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y %H:%M"))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}


    def login(self, user, data, req):
        html = req.load('http://euroshare.eu/customer-zone/login/',
                        post={"trvale": "1",
                              "login": user,
                              "password": data['password']},
                        decode=True)

        if u">Nesprávne prihlasovacie meno alebo heslo" in html:
            self.wrongPassword()
