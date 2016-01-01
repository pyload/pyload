# -*- coding: utf-8 -*-

from module.plugins.internal.MultiAccount import MultiAccount
from module.plugins.internal.misc import json


class PremiumizeMe(MultiAccount):
    __name__    = "PremiumizeMe"
    __type__    = "account"
    __version__ = "0.24"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Premiumize.me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Florian Franzen", "FlorianFranzen@gmail.com")]


    def grab_hosters(self, user, password, data):
        #: Get supported hosters list from premiumize.me using the
        #: json API v1 (see https://secure.premiumize.me/?show=api)
        answer = self.load("http://api.premiumize.me/pm-api/v1.php",  #@TODO: Revert to `https` in 0.4.10
                           get={'method'       : "hosterlist",
                                'params[login]': user,
                                'params[pass]' : password})
        data = json.loads(answer)

        #: If account is not valid thera are no hosters available
        if data['status'] != 200:
            return []

        #: Extract hosters from json file
        return data['result']['hosterlist']


    def grab_info(self, user, password, data):
        #: Get user data from premiumize.me
        status = self.get_account_status(user, password)
        self.log_debug(status)

        #: Parse account info
        account_info = {'validuntil': float(status['result']['expires']),
                        'trafficleft': max(0, status['result']['trafficleft_bytes'] / 1024)}  #@TODO: Remove `/ 1024` in 0.4.10

        if status['result']['type'] != 'free':
            account_info['premium'] = True

        return account_info


    def signin(self, user, password, data):
        #: Get user data from premiumize.me
        status = self.get_account_status(user, password)

        #: Check if user and password are valid
        if status['status'] != 200:
            self.fail_login()


    def get_account_status(self, user, password):
        #: Use premiumize.me API v1 (see https://secure.premiumize.me/?show=api)
        #: To retrieve account info and return the parsed json answer
        answer = self.load("http://api.premiumize.me/pm-api/v1.php",  #@TODO: Revert to `https` in 0.4.10
                           get={'method'       : "accountstatus",
                                'params[login]': user,
                                'params[pass]' : password})
        return json.loads(answer)
