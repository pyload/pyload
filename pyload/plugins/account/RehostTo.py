# -*- coding: utf-8 -*-

from pyload.plugins.Account import Account


class RehostTo(Account):
    __name    = "RehostTo"
    __type    = "account"
    __version = "0.10"

    __description = """Rehost.to account plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        page = req.load("http://rehost.to/api.php",
                        get={'cmd': "login", 'user': user, 'pass': data['password']})
        data = [x.split("=") for x in page.split(",")]
        ses = data[0][1]
        long_ses = data[1][1]

        page = req.load("http://rehost.to/api.php",
                        get={'cmd': "get_premium_credits", 'long_ses': long_ses})
        traffic, valid = page.split(",")

        account_info = {"trafficleft": int(traffic) * 1024,
                        "validuntil": int(valid),
                        "long_ses": long_ses,
                        "ses": ses}

        return account_info


    def login(self, user, data, req):
        page = req.load("http://rehost.to/api.php",
                        get={'cmd': "login", 'user': user, 'pass': data['password']})

        if "Login failed." in page:
            self.wrongPassword()
