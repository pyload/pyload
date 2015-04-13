# -*- coding: utf-8 -*-

import time

try:
    from beaker.crypto.pbkdf2 import PBKDF2

except ImportError:
    from beaker.crypto.pbkdf2 import pbkdf2
    from binascii import b2a_hex
    class PBKDF2(object):
        def __init__(self, passphrase, salt, iterations=1000):
            self.passphrase = passphrase
            self.salt = salt
            self.iterations = iterations

        def hexread(self, octets):
            return b2a_hex(pbkdf2(self.passphrase, self.salt, self.iterations, octets))

from module.common.json_layer import json_loads
from module.plugins.Account import Account


class OboomCom(Account):
    __name__    = "OboomCom"
    __type__    = "account"
    __version__ = "0.24"

    __description__ = """Oboom.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stanley", "stanley.foerster@gmail.com")]


    def loadAccountData(self, user, req):
        passwd = self.getAccountData(user)['password']
        salt   = passwd[::-1]
        pbkdf2 = PBKDF2(passwd, salt, 1000).hexread(16)

        result = json_loads(req.load("https://www.oboom.com/1/login", get={"auth": user, "pass": pbkdf2}))

        if not result[0] == 200:
            self.logWarning(_("Failed to log in: %s") % result[1])
            self.wrongPassword()

        return result[1]


    def loadAccountInfo(self, name, req):
        accountData = self.loadAccountData(name, req)

        userData = accountData['user']

        if userData['premium'] == "null":
            premium = False
        else:
            premium = True

        if userData['premium_unix'] == "null":
            validUntil = -1
        else:
            validUntil = float(userData['premium_unix'])

        traffic = userData['traffic']

        trafficLeft = traffic['current'] / 1024  #@TODO: Remove `/ 1024` in 0.4.10
        maxTraffic = traffic['max'] / 1024  #@TODO: Remove `/ 1024` in 0.4.10

        session = accountData['session']

        return {'premium'    : premium,
                'validuntil' : validUntil,
                'trafficleft': trafficLeft,
                'maxtraffic' : maxTraffic,
                'session'    : session}


    def login(self, user, data, req):
        self.loadAccountData(user, req)
