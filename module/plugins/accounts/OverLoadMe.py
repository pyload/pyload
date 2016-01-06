# -*- coding: utf-8 -*-

from module.plugins.internal.MultiAccount import MultiAccount
from module.plugins.internal.misc import json


class OverLoadMe(MultiAccount):
    __name__    = "OverLoadMe"
    __type__    = "account"
    __version__ = "0.11"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Over-Load.me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def grab_hosters(self, user, password, data):
        html = self.load("https://api.over-load.me/hoster.php",
                         get={'auth': "0001-cb1f24dadb3aa487bda5afd3b76298935329be7700cd7-5329be77-00cf-1ca0135f"})
        return [x for x in map(str.strip, html.replace("\"", "").split(",")) if x]


    def grab_info(self, user, password, data):
        html  = self.load("https://api.over-load.me/account.php",
                          get={'user': user,
                               'auth': password}).strip()

        data = json.loads(html)
        self.log_debug(data)

        #: Check for premium
        if data['membership'] == "Free":
            return {'premium': False, 'validuntil': None, 'trafficleft': None}
        else:
            return {'premium': True, 'validuntil': data['expirationunix'], 'trafficleft': -1}


    def signin(self, user, password, data):
        html = self.load("https://api.over-load.me/account.php",
                         get={'user': user,
                              'auth': password}).strip()

        data = json.loads(html)

        if data['err'] == 1:
            self.fail_login()
