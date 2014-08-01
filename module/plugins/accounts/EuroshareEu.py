# -*- coding: utf-8 -*-

from time import mktime, strptime
import re

from module.plugins.Account import Account


class EuroshareEu(Account):
    __name__ = "EuroshareEu"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Euroshare.eu account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    def loadAccountInfo(self, user, req):
        self.relogin(user)
        html = req.load("http://euroshare.eu/customer-zone/settings/")

        m = re.search('id="input_expire_date" value="(\d+\.\d+\.\d+ \d+:\d+)"', html)
        if m is None:
            premium, validuntil = False, -1
        else:
            premium = True
            validuntil = mktime(strptime(m.group(1), "%d.%m.%Y %H:%M"))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def login(self, user, data, req):

        html = req.load('http://euroshare.eu/customer-zone/login/', post={
            "trvale": "1",
            "login": user,
            "password": data['password']
        }, decode=True)

        if u">Nesprávne prihlasovacie meno alebo heslo" in html:
            self.wrongPassword()
