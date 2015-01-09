# -*- coding: utf-8 -*-

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class OverLoadMe(Account):
    __name__    = "OverLoadMe"
    __type__    = "account"
    __version__ = "0.04"

    __description__ = """Over-Load.me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def loadAccountInfo(self, user, req):
        https = "https" if self.getConfig("ssl") else "http"
        data  = self.getAccountData(user)
        html  = req.load(https + "://api.over-load.me/account.php",
                         get={'user': user,
                              'auth': data['password']}).strip()

        data = json_loads(html)
        self.logDebug(data)

        # Check for premium
        if data['membership'] == "Free":
            return {'premium': False, 'validuntil': None, 'trafficleft': None}
        else:
            return {'premium': True, 'validuntil': data['expirationunix'], 'trafficleft': -1}


    def login(self, user, data, req):
        https    = "https" if self.getConfig("ssl") else "http"
        jsondata = req.load(https + "://api.over-load.me/account.php",
                            get={'user': user,
                                 'auth': data['password']}).strip()

        data = json_loads(jsondata)

        if data['err'] == 1:
            self.wrongPassword()
