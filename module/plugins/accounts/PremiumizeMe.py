# -*- coding: utf-8 -*-

import pycurl

from module.common.json_layer import json_loads
from module.plugins.Account import Account


class PremiumizeMe(Account):
    __name__    = "PremiumizeMe"
    __type__    = "account"
    __version__ = "0.14"

    __description__ = """Premiumize.me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Florian Franzen", "FlorianFranzen@gmail.com")]


    def getAccountRequest(self, user=None):
        req = super(PremiumizeMe, self).getAccountRequest(user)
        req.http.c.setopt(pycurl.CURLOPT_SSL_CIPHER_LIST, "TLSv1")
        return req


    def loadAccountInfo(self, user, req):
        # Get user data from premiumize.me
        status = self.getAccountStatus(user, req)
        self.logDebug(status)

        # Parse account info
        account_info = {"validuntil": float(status['result']['expires']),
                        "trafficleft": max(0, status['result']['trafficleft_bytes'] / 1024)}  #@TODO: Remove `/ 1024` in 0.4.10

        if status['result']['type'] == 'free':
            account_info['premium'] = False

        return account_info


    def login(self, user, data, req):
        # Get user data from premiumize.me
        status = self.getAccountStatus(user, req)

        # Check if user and password are valid
        if status['status'] != 200:
            self.wrongPassword()


    def getAccountStatus(self, user, req):
        # Use premiumize.me API v1 (see https://secure.premiumize.me/?show=api)
        # to retrieve account info and return the parsed json answer
        answer = req.load("https://api.premiumize.me/pm-api/v1.php",
                           get={'method'       : "accountstatus",
                                'params[login]': user,
                                'params[pass]' : self.getAccountData(user)['password']})
        return json_loads(answer)
