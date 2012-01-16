# -*- coding: utf-8 -*-
from module.plugins.MultiHoster import MultiHoster

class Premium4Me(MultiHoster):
    __name__ = "Premium4Me"
    __version__ = "0.10"
    __type__ = "account"
    __description__ = """Premium4.me account plugin"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    def loadAccountInfo(self, req):
        traffic = req.load("http://premium4.me/api/traffic.php?authcode=%s" % self.authcode)

        account_info = {"trafficleft": int(traffic) / 1024, "validuntil": -1}

        return account_info

    def login(self, req):
        self.authcode = req.load("http://premium4.me/api/getauthcode.php?username=%s&password=%s" % (self.loginname, self.password)).strip()

        if "wrong username" in self.authcode:
            self.wrongPassword()
        
    def loadHosterList(self, req):
        page = req.load("http://premium4.me/api/hosters.php?authcode=%s" % self.authcode)
        return [x.strip() for x in page.replace("\"", "").split(";")]