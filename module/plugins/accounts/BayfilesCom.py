# -*- coding: utf-8 -*-

from time import time

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class BayfilesCom(Account):
    __name__ = "BayfilesCom"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """Bayfiles.com account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    def loadAccountInfo(self, user, req):
        for _ in xrange(2):
            response = json_loads(req.load("http://api.bayfiles.com/v1/account/info"))
            self.logDebug(response)
            if not response['error']:
                break
            self.logWarning(response['error'])
            self.relogin(user)

        return {"premium": bool(response['premium']), "trafficleft": -1,
                "validuntil": response['expires'] if response['expires'] >= int(time()) else -1}

    def login(self, user, data, req):
        response = json_loads(req.load("http://api.bayfiles.com/v1/account/login/%s/%s" % (user, data['password'])))
        self.logDebug(response)
        if response['error']:
            self.logError(response['error'])
            self.wrongPassword()
