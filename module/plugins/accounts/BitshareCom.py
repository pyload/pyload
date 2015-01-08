# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class BitshareCom(Account):
    __name__    = "BitshareCom"
    __type__    = "account"
    __version__ = "0.13"

    __description__ = """Bitshare account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Paul King", None)]


    def loadAccountInfo(self, user, req):
        html = req.load("http://bitshare.com/mysettings.html")

        if "\"http://bitshare.com/myupgrade.html\">Free" in html:
            return {"validuntil": -1, "trafficleft": -1, "premium": False}

        if not '<input type="checkbox" name="directdownload" checked="checked" />' in html:
            self.logWarning(_("Activate direct Download in your Bitshare Account"))

        return {"validuntil": -1, "trafficleft": -1, "premium": True}


    def login(self, user, data, req):
        html = req.load("http://bitshare.com/login.html",
                        post={"user": user, "password": data['password'], "submit": "Login"},
                        cookies=True,
                        decode=True)

        if "login" in req.lastEffectiveURL:
            self.wrongPassword()
