# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account


class RehostTo(Account):
    __name__    = "RehostTo"
    __type__    = "account"
    __version__ = "0.18"
    __status__  = "testing"

    __description__ = """Rehost.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def parse_info(self, user, password, data, req):
        premium     = False
        trafficleft = None
        validuntil  = -1
        session     = ""

        html = self.load("https://rehost.to/api.php",
                        get={'cmd' : "login",
                             'user': user,
                             'pass': password})
        try:
            session = html.split(",")[1].split("=")[1]

            html = self.load("http://rehost.to/api.php",
                             get={'cmd'     : "get_premium_credits",
                                  'long_ses': session})

            if html.strip() == "0,0" or "ERROR" in html:
                self.log_debug(html)
            else:
                traffic, valid = html.split(",")

                premium     = True
                trafficleft = self.parse_traffic(traffic + "MB")
                validuntil  = float(valid)

        finally:
            return {'premium'    : premium,
                    'trafficleft': trafficleft,
                    'validuntil' : validuntil,
                    'session'    : session}


    def login(self, user, password, data, req):
        html = self.load("https://rehost.to/api.php",
                         get={'cmd': "login",
                              'user': user,
                              'pass': password})

        if "ERROR" in html:
            self.log_debug(html)
            self.login_fail()
