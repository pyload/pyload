# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class FourSharedCom(Account):
    __name__    = "FourSharedCom"
    __type__    = "account"
    __version__ = "0.04"

    __description__ = """FourShared.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def loadAccountInfo(self, user, req):
        # Free mode only for now
        return {"premium": False}


    def login(self, user, data, req):
        req.cj.setCookie("4shared.com", "4langcookie", "en")

        res = req.load("http://www.4shared.com/web/login",
                       post={'login'    : user,
                             'password' : data['password'],
                             'remember' : "on",
                             '_remember': "on",
                             'returnTo' : "http://www.4shared.com/account/home.jsp"},
                       decode=True)

        if 'Please log in to access your 4shared account' in res:
            self.wrongPassword()
