# -*- coding: utf-8 -*-

from pyload.plugins.Account import Account


class PremiumTo(Account):
    __name__ = "PremiumTo"
    __type__ = "account"
    __version__ = "0.04"

    __description__ = """Premium.to account plugin"""
    __author_name__ = ("RaNaN", "zoidberg", "stickell")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz", "l.stickell@yahoo.it")


    def loadAccountInfo(self, user, req):
        api_r = req.load("http://premium.to/api/straffic.php",
                         get={'username': self.username, 'password': self.password})
        traffic = sum(map(int, api_r.split(';')))

        return {"trafficleft": int(traffic) / 1024, "validuntil": -1}

    def login(self, user, data, req):
        self.username = user
        self.password = data['password']
        authcode = req.load("http://premium.to/api/getauthcode.php?username=%s&password=%s" % (
                                 user, self.password)).strip()

        if "wrong username" in authcode:
            self.wrongPassword()
