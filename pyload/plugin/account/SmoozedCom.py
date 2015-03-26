# -*- coding: utf-8 -*-

import hashlib
import time

from beaker.crypto.pbkdf2 import PBKDF2

from pyload.utils import json_loads
from pyload.plugin.Account import Account


class SmoozedCom(Account):
    __name    = "SmoozedCom"
    __type    = "account"
    __version = "0.03"

    __description = """Smoozed.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("", "")]


    def loadAccountInfo(self, user, req):
        # Get user data from premiumize.me
        status = self.getAccountStatus(user, req)

        self.logDebug(status)

        if status['state'] != 'ok':
            info = {'validuntil' : None,
                    'trafficleft': None,
                    'premium'    : False}
        else:
            # Parse account info
            info = {'validuntil' : float(status["data"]["user"]["user_premium"]),
                    'trafficleft': max(0, status["data"]["traffic"][1] - status["data"]["traffic"][0]),
                    'session'    : status["data"]["session_key"],
                    'hosters'    : [hoster["name"] for hoster in status["data"]["hoster"]]}

            if info['validuntil'] < time.time():
                info['premium'] = False
            else:
                info['premium'] = True

        return info


    def login(self, user, data, req):
        # Get user data from premiumize.me
        status = self.getAccountStatus(user, req)

        # Check if user and password are valid
        if status['state'] != 'ok':
            self.wrongPassword()


    def getAccountStatus(self, user, req):
        password  = self.getAccountData(user)['password']
        salt      = hashlib.sha256(password).hexdigest()
        encrypted = PBKDF2(password, salt, iterations=1000).hexread(32)

        return json_loads(req.load("http://www2.smoozed.com/api/login",
                                   get={'auth': user, 'password': encrypted}))
