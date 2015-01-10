# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class RehostTo(Account):
    __name__    = "RehostTo"
    __type__    = "account"
    __version__ = "0.14"

    __description__ = """Rehost.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        html = req.load("http://rehost.to/api.php",
                        get={'cmd': "login", 'user': user, 'pass': data['password']})

        session = [x.split("=") for x in html.split(",")][1][1]

        html = req.load("http://rehost.to/api.php",
                        get={'cmd': "get_premium_credits", 'long_ses': session})

        traffic, valid = html.split(",")

        trafficleft = self.parseTraffic(traffic + "MB")
        validuntil  = float(valid)

        return {'trafficleft': trafficleft,
                'validuntil' : validuntil,
                'session'    : session}


    def login(self, user, data, req):
        html = req.load("http://rehost.to/api.php",
                        get={'cmd': "login", 'user': user, 'pass': data['password']},
                        decode=True)

        if "Login failed." in html:
            self.wrongPassword()
