# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account


class PremiumTo(Account):
    __name__    = "PremiumTo"
    __type__    = "account"
    __version__ = "0.11"
    __status__  = "testing"

    __description__ = """Premium.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def parse_info(self, user, password, data, req):
        traffic = self.load("http://premium.to/api/straffic.php",  #@TODO: Revert to `https` in 0.4.10
                            get={'username': self.username,
                                 'password': self.password})

        if "wrong username" not in traffic:
            trafficleft = sum(map(float, traffic.split(';'))) / 1024  #@TODO: Remove `/ 1024` in 0.4.10
            return {'premium': True, 'trafficleft': trafficleft, 'validuntil': -1}
        else:
            return {'premium': False, 'trafficleft': None, 'validuntil': None}


    def login(self, user, password, data, req):
        self.username = user
        self.password = password
        authcode = self.load("http://premium.to/api/getauthcode.php",  #@TODO: Revert to `https` in 0.4.10
                             get={'username': user,
                                  'password': self.password})

        if "wrong username" in authcode:
            self.login_fail()
