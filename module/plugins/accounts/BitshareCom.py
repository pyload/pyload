# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account


class BitshareCom(Account):
    __name__    = "BitshareCom"
    __type__    = "account"
    __version__ = "0.15"
    __status__  = "testing"

    __description__ = """Bitshare account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Paul King", None)]


    def parse_info(self, user, password, data, req):
        html = self.load("http://bitshare.com/mysettings.html")

        if "\"http://bitshare.com/myupgrade.html\">Free" in html:
            return {'validuntil': -1, 'trafficleft': -1, 'premium': False}

        if not '<input type="checkbox" name="directdownload" checked="checked" />' in html:
            self.log_warning(_("Activate direct Download in your Bitshare Account"))

        return {'validuntil': -1, 'trafficleft': -1, 'premium': True}


    def login(self, user, password, data, req):
        html = self.load("https://bitshare.com/login.html",
                         post={'user'    : user,
                               'password': password,
                               'submit'  : "Login"})

        if "login" in req.lastEffectiveURL:
            self.login_fail()
