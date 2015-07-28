# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class RPNetBiz(Account):
    __name__    = "RPNetBiz"
    __type__    = "account"
    __version__ = "0.15"
    __status__  = "testing"

    __description__ = """RPNet.biz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Dman", "dmanugm@gmail.com")]


    def parse_info(self, user, password, data, req):
        #: Get account information from rpnet.biz
        res = self.get_account_status(user, password, req)
        try:
            if res['accountInfo']['isPremium']:
                #: Parse account info. Change the trafficleft later to support per host info.
                account_info = {'validuntil': float(res['accountInfo']['premiumExpiry']),
                                'trafficleft': -1, 'premium': True}
            else:
                account_info = {'validuntil': None, 'trafficleft': None, 'premium': False}

        except KeyError:
            #: Handle wrong password exception
            account_info = {'validuntil': None, 'trafficleft': None, 'premium': False}

        return account_info


    def login(self, user, password, data, req):
        #: Get account information from rpnet.biz
        res = self.get_account_status(user, password, req)

        #: If we have an error in the res, we have wrong login information
        if 'error' in res:
            self.login_fail()


    def get_account_status(self, user, password, req):
        #: Using the rpnet API, check if valid premium account
        res = self.load("https://premium.rpnet.biz/client_api.php",
                            get={'username': user, 'password': password,
                                 'action': "showAccountInformation"})
        self.log_debug("JSON data: %s" % res)

        return json_loads(res)
