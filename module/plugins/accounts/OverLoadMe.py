# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class OverLoadMe(Account):
    __name__    = "OverLoadMe"
    __type__    = "account"
    __version__ = "0.06"
    __status__  = "testing"

    __description__ = """Over-Load.me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def parse_info(self, user, password, data, req):
        data  = self.get_data(user)
        html  = self.load("https://api.over-load.me/account.php",
                          get={'user': user,
                               'auth': password}).strip()

        data = json_loads(html)
        self.log_debug(data)

        #: Check for premium
        if data['membership'] == "Free":
            return {'premium': False, 'validuntil': None, 'trafficleft': None}
        else:
            return {'premium': True, 'validuntil': data['expirationunix'], 'trafficleft': -1}


    def login(self, user, password, data, req):
        jsondata = self.load("https://api.over-load.me/account.php",
                             get={'user': user,
                                  'auth': password}).strip()

        data = json_loads(jsondata)

        if data['err'] == 1:
            self.login_fail()
