# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account


class BitshareCom(Account):
    __name    = "BitshareCom"
    __type    = "account"
    __version = "0.13"

    __description = """Bitshare account plugin"""
    __license     = "GPLv3"
    __authors     = [("Paul King", "")]


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
                        decode=True)

        if "login" in req.lastEffectiveURL:
            self.wrongPassword()
