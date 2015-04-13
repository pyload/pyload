# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class OverLoadMe(Account):
    __name    = "OverLoadMe"
    __type    = "account"
    __version = "0.04"

    __description = """Over-Load.me account plugin"""
    __license     = "GPLv3"
    __authors     = [("marley", "marley@over-load.me")]


    def loadAccountInfo(self, user, req):
        https = "https" if self.getConfig('ssl') else "http"
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
        https    = "https" if self.getConfig('ssl') else "http"
        jsondata = req.load(https + "://api.over-load.me/account.php",
                            get={'user': user,
                                 'auth': data['password']}).strip()

        data = json_loads(jsondata)

        if data['err'] == 1:
            self.wrongPassword()
