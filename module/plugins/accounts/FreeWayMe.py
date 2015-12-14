# -*- coding: utf-8 -*-

from module.plugins.internal.MultiAccount import MultiAccount
from module.plugins.internal.misc import json


class FreeWayMe(MultiAccount):
    __name__    = "FreeWayMe"
    __type__    = "account"
    __version__ = "0.21"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """FreeWayMe account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def grab_hosters(self, user, password, data):
        html = self.load("http://www.free-way.bz/ajax/jd.php",
                         get={'id'  : 3, 'user': user, 'pass': password})  #@TODO: Revert to `https` in 0.4.10
        return [x for x in map(str.strip, html.replace("\"", "").split(",")) if x]


    def grab_info(self, user, password, data):
        status = self.get_account_status(user, password)

        self.log_debug(status)

        account_info = {'validuntil': -1, 'premium': False}
        if status['premium'] == "Free":
            account_info['trafficleft'] = self.parse_traffic(status['guthaben'], "MB")
        elif status['premium'] == "Spender":
            account_info['trafficleft'] = -1
        elif status['premium'] == "Flatrate":
            account_info = {'validuntil' : float(status['Flatrate']),
                            'trafficleft': -1,
                            'premium'    : True}

        return account_info


    def signin(self, user, password, data):
        status = self.get_account_status(user, password)

        #: Check if user and password are valid
        if not status:
            self.fail_login()


    def get_account_status(self, user, password):
        answer = self.load("http://www.free-way.bz/ajax/jd.php",  #@TODO: Revert to `https` in 0.4.10
                          get={'id': 4, 'user': user, 'pass': password})

        self.log_debug("Login: %s" % answer)

        if answer == "Invalid login":
            self.fail_login()

        return json.loads(answer)
