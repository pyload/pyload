# -*- coding: utf-8 -*-

from ..internal.MultiAccount import MultiAccount


class PremiumTo(MultiAccount):
    __name__ = "PremiumTo"
    __type__ = "account"
    __version__ = "0.18"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Premium.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.org"),
                   ("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_FAILED_PATTERN = r'wrong username'

    API_URL = "http://api.premium.to/api/"

    def api_response(self, method, user, password):
        return self.load(self.API_URL + method + ".php",
                         get={'username': user,
                              'password': password})

    def grab_hosters(self, user, password, data):
        html = self.api_response("hosters", user, password)
        return [x.strip() for x in html.replace("\"", "").split(";") if x] \
            if self.LOGIN_FAILED_PATTERN not in html else []

    def grab_info(self, user, password, data):
        traffic = self.api_response("straffic", user, password)

        if self.LOGIN_FAILED_PATTERN not in traffic:
            # @TODO: Remove `/ 1024` in 0.4.10
            trafficleft = sum(map(float, traffic.split(';'))) / 1024
            return {'premium': True, 'trafficleft': trafficleft, 'validuntil': -1}

        else:
            return {'premium': False, 'trafficleft': None, 'validuntil': None}

    def signin(self, user, password, data):
        authcode = self.api_response("getauthcode", user, password)

        if self.LOGIN_FAILED_PATTERN in authcode:
            self.fail_login()
