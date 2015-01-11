# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class UploadableCh(Account):
    __name__    = "UploadableCh"
    __type__    = "account"
    __version__ = "0.03"

    __description__ = """Uploadable.ch account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Sasch", "gsasch@gmail.com")]


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.uploadable.ch/login.php")

        premium     = '<a href="/logout.php"' in html
        trafficleft = -1 if premium else None

        return {'validuntil': None, 'trafficleft': trafficleft, 'premium': premium}  #@TODO: validuntil


    def login(self, user, data, req):
        html = req.load("http://www.uploadable.ch/login.php",
                        post={'userName'     : user,
                              'userPassword' : data["password"],
                              'autoLogin'    : "1",
                              'action__login': "normalLogin"},
                        decode=True)

        if "Login failed" in html:
            self.wrongPassword()
