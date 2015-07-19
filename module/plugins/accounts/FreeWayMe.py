# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class FreeWayMe(Account):
    __name__    = "FreeWayMe"
    __type__    = "account"
    __version__ = "0.16"

    __description__ = """FreeWayMe account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def load_account_info(self, user, req):
        status = self.get_account_status(user, req)

        self.log_debug(status)

        account_info = {'validuntil': -1, 'premium': False}
        if status['premium'] == "Free":
            account_info['trafficleft'] = self.parse_traffic(status['guthaben'] + "MB")
        elif status['premium'] == "Spender":
            account_info['trafficleft'] = -1
        elif status['premium'] == "Flatrate":
            account_info = {'validuntil' : float(status['Flatrate']),
                            'trafficleft': -1,
                            'premium'    : True}

        return account_info


    def login(self, user, data, req):
        status = self.get_account_status(user, req)

        #: Check if user and password are valid
        if not status:
            self.wrong_password()


    def get_account_status(self, user, req):
        answer = self.load("http://www.free-way.bz/ajax/jd.php",  #@TODO: Revert to `https` in 0.4.10
                          get={'id': 4, 'user': user, 'pass': self.get_account_data(user)['password']})

        self.log_debug("Login: %s" % answer)

        if answer == "Invalid login":
            self.wrong_password()

        return json_loads(answer)
