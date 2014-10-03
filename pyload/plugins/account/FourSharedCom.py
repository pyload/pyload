# -*- coding: utf-8 -*-

from pyload.plugins.base.Account import Account
from pyload.utils import json_loads


class FourSharedCom(Account):
    __name__ = "FourSharedCom"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """FourShared.com account plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")


    def loadAccountInfo(self, user, req):
        # Free mode only for now
        return {"premium": False}

    def login(self, user, data, req):
        req.cj.setCookie("4shared.com", "4langcookie", "en")
        response = req.load('http://www.4shared.com/web/login',
                            post={"login": user,
                                  "password": data['password'],
                                  "remember": "on",
                                  "_remember": "on",
                                  "returnTo": "http://www.4shared.com/account/home.jsp"})

        if 'Please log in to access your 4shared account' in response:
            self.wrongPassword()
