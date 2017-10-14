# -*- coding: utf-8 -*-

from ..internal.MultiAccount import MultiAccount


class RehostTo(MultiAccount):
    __name__ = "RehostTo"
    __type__ = "account"
    __version__ = "0.25"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Rehost.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.org")]

    def grab_hosters(self, user, password, data):
        html = self.load("http://rehost.to/api.php",
                         get={'cmd': "get_supported_och_dl",
                              'long_ses': data['session']})
        return [x for x in map(
            str.strip, html.replace("\"", "").split(",")) if x]

    def grab_info(self, user, password, data):
        premium = False
        trafficleft = None
        validuntil = -1
        session = ""

        html = self.load("https://rehost.to/api.php",
                         get={'cmd': "login",
                              'user': user,
                              'pass': password})
        try:
            session = html.split(",")[1].split("=")[1]

            html = self.load("http://rehost.to/api.php",
                             get={'cmd': "get_premium_credits",
                                  'long_ses': session})

            if html.strip() == "0,0" or "ERROR" in html:
                self.log_debug(html)
            else:
                traffic, valid = html.split(",")

                premium = True
                trafficleft = self.parse_traffic(traffic, "MB")
                validuntil = float(valid)

        finally:
            return {'premium': premium,
                    'trafficleft': trafficleft,
                    'validuntil': validuntil,
                    'session': session}

    def signin(self, user, password, data):
        html = self.load("https://rehost.to/api.php",
                         get={'cmd': "login",
                              'user': user,
                              'pass': password})

        if "ERROR" in html:
            self.log_debug(html)
            self.fail_login()
