# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class Premium4Me(Account):
    __name__ = "Premium4Me"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """Premium.to account plugin"""
    __author_name__ = ("RaNaN", "zoidberg", "stickell")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz", "l.stickell@yahoo.it")


    def loadAccountInfo(self, user, req):
        traffic = req.load("http://premium.to/api/traffic.php?authcode=%s" % self.authcode)

        account_info = {"trafficleft": int(traffic) / 1024,
                        "validuntil": -1}

        return account_info

    def login(self, user, data, req):
        self.authcode = req.load("http://premium.to/api/getauthcode.php?username=%s&password=%s" % (
                                 user, data['password'])).strip()

        if "wrong username" in self.authcode:
            self.wrongPassword()
