# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class BitshareCom(Account):
    __name__ = "BitshareCom"
    __type__ = "account"
    __version__ = "0.12"

    __description__ = """Bitshare account plugin"""
    __author_name__ = "Paul King"
    __author_mail__ = None


    def loadAccountInfo(self, user, req):
        page = req.load("http://bitshare.com/mysettings.html")

        if "\"http://bitshare.com/myupgrade.html\">Free" in page:
            return {"validuntil": -1, "trafficleft": -1, "premium": False}

        if not '<input type="checkbox" name="directdownload" checked="checked" />' in page:
            self.logWarning(_("Activate direct Download in your Bitshare Account"))

        return {"validuntil": -1, "trafficleft": -1, "premium": True}

    def login(self, user, data, req):
        page = req.load("http://bitshare.com/login.html",
                        post={"user": user, "password": data['password'], "submit": "Login"}, cookies=True)
        if "login" in req.lastEffectiveURL:
            self.wrongPassword()
