# -*- coding: utf-8 -*-

from time import time

from pyload.plugins.internal.Account import Account
from pyload.utils import json_loads


class BayfilesCom(Account):
    __name__    = "BayfilesCom"
    __type__    = "account"
    __version__ = "0.03"

    __description__ = """Bayfiles.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def loadAccountInfo(self, user, req):
        for _i in xrange(2):
            res = json_loads(req.load("http://api.bayfiles.com/v1/account/info"))
            self.logDebug(res)
            if not res['error']:
                break
            self.logWarning(res['error'])
            self.relogin(user)

        return {"premium": bool(res['premium']), "trafficleft": -1,
                "validuntil": res['expires'] if res['expires'] >= int(time()) else -1}


    def login(self, user, data, req):
        res = json_loads(req.load("http://api.bayfiles.com/v1/account/login/%s/%s" % (user, data['password'])))
        self.logDebug(res)
        if res['error']:
            self.logError(res['error'])
            self.wrongPassword()
