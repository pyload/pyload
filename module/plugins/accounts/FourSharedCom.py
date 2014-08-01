# -*- coding: utf-8 -*-

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class FourSharedCom(Account):
    __name__ = "FourSharedCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """FourShared.com account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    def loadAccountInfo(self, user, req):
        #fixme
        return {"validuntil": -1, "trafficleft": -1, "premium": False}

    def login(self, user, data, req):
        req.cj.setCookie("www.4shared.com", "4langcookie", "en")
        response = req.load('http://www.4shared.com/login',
                            post={"login": user,
                                  "password": data['password'],
                                  "remember": "false",
                                  "doNotRedirect": "true"})
        self.logDebug(response)
        response = json_loads(response)

        if not "ok" in response or response['ok'] != True:
            if "rejectReason" in response and response['rejectReason'] != True:
                self.logError(response['rejectReason'])
            self.wrongPassword()
