# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.Account import Account


class PremiumizeMe(Account):
    __name__    = "PremiumizeMe"
    __type__    = "account"
    __version__ = "0.19"
    __status__  = "stable"

    __description__ = """Premiumize.me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Florian Franzen", "FlorianFranzen@gmail.com")]


    def load_account_info(self, user, req):
        #: Get user data from premiumize.me
        status = self.get_account_status(user, req)
        self.log_debug(status)

        #: Parse account info
        account_info = {'validuntil': float(status['result']['expires']),
                        'trafficleft': max(0, status['result']['trafficleft_bytes'] / 1024)}  #@TODO: Remove `/ 1024` in 0.4.10

        if status['result']['type'] != 'free':
            account_info['premium'] = True

        return account_info


    def login(self, user, data, req):
        #: Get user data from premiumize.me
        status = self.get_account_status(user, req)

        #: Check if user and password are valid
        if status['status'] != 200:
            self.wrong_password()


    def get_account_status(self, user, req):
        #: Use premiumize.me API v1 (see https://secure.premiumize.me/?show=api)
        #: To retrieve account info and return the parsed json answer
        answer = self.load("http://api.premiumize.me/pm-api/v1.php",  #@TODO: Revert to `https` in 0.4.10
                           get={'method'       : "accountstatus",
                                'params[login]': user,
                                'params[pass]' : self.get_account_data(user)['password']})
        return json_loads(answer)
