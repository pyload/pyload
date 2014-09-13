# -*- coding: utf-8 -*-

import time

from module.lib.beaker.crypto.pbkdf2 import PBKDF2

from module.common.json_layer import json_loads
from module.plugins.Account import Account


class OboomCom(Account):
    __name__ = "OboomCom"
    __type__ = "account"
    __version__ = "0.1"

    __description__ = """Oboom.com account plugin"""
    __author_name__ = "stanley"
    __author_mail__ = "stanley.foerster@gmail.com"


    def loadAccountData(self, user, req):
        passwd = self.getAccountData(user)['password']
        salt = passwd[::-1]
        pbkdf2 = PBKDF2(passwd, salt, 1000).hexread(16)
        result = json_loads(req.load("https://www.oboom.com/1.0/login", get={"auth": user, "pass": pbkdf2}))
        if not result[0] == 200:
            self.logWarning("Failed to log in: %s" % result[1])
            self.wrongPassword()
        return result[1]

    def loadAccountInfo(self, name, req):
        accountData = self.loadAccountData(name, req)
        userData = accountData['user']

        if "premium_unix" in userData:
            validUntilUtc = int(userData['premium_unix'])
            if validUntilUtc > int(time.time()):
                premium = True
                validUntil = validUntilUtc
                traffic = userData['traffic']
                trafficLeft = traffic['current']
                maxTraffic = traffic['max']
                session = accountData['session']
                return {"premium": premium,
                        "validuntil": validUntil,
                        "trafficleft": trafficLeft / 1024,
                        "maxtraffic": maxTraffic / 1024,
                        "session": session
                }
        return {"premium": False, "validuntil": -1}

    def login(self, user, data, req):
        self.loadAccountData(user, req)
