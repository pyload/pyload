from module.plugins.Account import Account

class Premium4Me(Account):
    __name__ = "Premium4Me"
    __version__ = "0.02"
    __type__ = "account"
    __description__ = """Premium4.me account plugin"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    def loadAccountInfo(self, user, req):
        traffic = req.load("http://premium4.me/api/traffic.php?authcode=%s" % self.authcode)

        account_info = {"trafficleft": int(traffic) / 1024,
                        "validuntil": -1}

        return account_info

    def login(self, user, data, req):
        self.authcode = req.load("http://premium4.me/api/getauthcode.php?username=%s&password=%s" % (user, data["password"])).strip()
        
        if "wrong username" in self.authcode:
            self.wrongPassword()