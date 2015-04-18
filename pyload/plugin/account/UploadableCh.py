# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account


class UploadableCh(Account):
    __name    = "UploadableCh"
    __type    = "account"
    __version = "0.03"

    __description = """Uploadable.ch account plugin"""
    __license     = "GPLv3"
    __authors     = [("Sasch", "gsasch@gmail.com")]


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.uploadable.ch/login.php")

        premium     = '<a href="/logout.php"' in html
        trafficleft = -1 if premium else None

        return {'validuntil': None, 'trafficleft': trafficleft, 'premium': premium}  #@TODO: validuntil


    def login(self, user, data, req):
        html = req.load("http://www.uploadable.ch/login.php",
                        post={'userName'     : user,
                              'userPassword' : data['password'],
                              'autoLogin'    : "1",
                              'action__login': "normalLogin"},
                        decode=True)

        if "Login failed" in html:
            self.wrongPassword()
