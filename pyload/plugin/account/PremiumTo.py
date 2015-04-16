# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account


class PremiumTo(Account):
    __name    = "PremiumTo"
    __type    = "account"
    __version = "0.08"

    __description = """Premium.to account plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def loadAccountInfo(self, user, req):
        traffic = req.load("http://premium.to/api/straffic.php",
                           get={'username': self.username, 'password': self.password})

        if "wrong username" not in traffic:
            trafficleft = sum(map(float, traffic.split(';')))
            return {'premium': True, 'trafficleft': trafficleft, 'validuntil': -1}
        else:
            return {'premium': False, 'trafficleft': None, 'validuntil': None}


    def login(self, user, data, req):
        self.username = user
        self.password = data['password']
        authcode = req.load("http://premium.to/api/getauthcode.php",
                            get={'username': user, 'password': self.password},
                            decode=True)

        if "wrong username" in authcode:
            self.wrongPassword()
