# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class RehostTo(Account):
    __name__ = "RehostTo"
    __type__ = "account"
    __version__ = "0.1"

    __description__ = """Rehost.to account plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        page = req.load("http://rehost.to/api.php?cmd=login&user=%s&pass=%s" % (user, data['password']))
        data = [x.split("=") for x in page.split(",")]
        ses = data[0][1]
        long_ses = data[1][1]

        page = req.load("http://rehost.to/api.php?cmd=get_premium_credits&long_ses=%s" % long_ses)
        traffic, valid = page.split(",")

        account_info = {"trafficleft": int(traffic) * 1024,
                        "validuntil": int(valid),
                        "long_ses": long_ses,
                        "ses": ses}

        return account_info

    def login(self, user, data, req):
        page = req.load("http://rehost.to/api.php?cmd=login&user=%s&pass=%s" % (user, data['password']))

        if "Login failed." in page:
            self.wrongPassword()
