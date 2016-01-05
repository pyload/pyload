# -*- coding: utf-8 -*-

from module.plugins.internal.MultiAccount import MultiAccount


class PremiumTo(MultiAccount):
    __name__    = "PremiumTo"
    __type__    = "account"
    __version__ = "0.15"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Premium.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def grab_hosters(self, user, password, data):
        html = self.load("http://premium.to/api/hosters.php",
                         get={'username': user, 'password': password})
        return [x for x in map(str.strip, html.replace("\"", "").split(",")) if x]


    def grab_info(self, user, password, data):
        traffic = self.load("http://premium.to/api/straffic.php",  #@TODO: Revert to `https` in 0.4.10
                            get={'username': user,
                                 'password': password})

        if "wrong username" not in traffic:
            trafficleft = sum(map(float, traffic.split(';'))) / 1024  #@TODO: Remove `/ 1024` in 0.4.10
            return {'premium': True, 'trafficleft': trafficleft, 'validuntil': -1}
        else:
            return {'premium': False, 'trafficleft': None, 'validuntil': None}


    def signin(self, user, password, data):
        authcode = self.load("http://premium.to/api/getauthcode.php",  #@TODO: Revert to `https` in 0.4.10
                             get={'username': user,
                                  'password': password})

        if "wrong username" in authcode:
            self.fail_login()
