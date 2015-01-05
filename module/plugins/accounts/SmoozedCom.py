# -*- coding: utf-8 -*-

from module.plugins.Account import Account

from module.common.json_layer import json_loads

from time import time

import hashlib
from beaker.crypto.pbkdf2 import PBKDF2



class SmoozedCom(Account):
    __name__    = "SmoozedCom"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """Smoozed.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = []


    def loadAccountInfo(self, user, req):
        # Get user data from premiumize.me
        status = self.getAccountStatus(user, req)
        self.logDebug(status)

        # Parse account info
        account_info = {"validuntil": float(status["data"]["user"]["user_premium"]),
                        "trafficleft": max(0, status["data"]["traffic"][1] - status["data"]["traffic"][0]),
                        "session_key": status["data"]["session_key"],
                        "hoster": [hoster["name"] for hoster in status["data"]["hoster"]]}

        if account_info["validuntil"] < time():
            account_info['premium'] = False
        else:
            account_info['premium'] = True

        return account_info

    def login(self, user, data, req):
        # Get user data from premiumize.me
        status = self.getAccountStatus(user, req)

        # Check if user and password are valid
        if status['state'] != 'ok':
            self.wrongPassword()

    def getAccountStatus(self, user, req):
        salt = hashlib.sha256(self.accounts[user]['password']).hexdigest()
        encrypted = PBKDF2(self.accounts[user]['password'], salt, iterations=1000).hexread(32)
        answer = req.load('http://www2.smoozed.com/api/login?auth=%s&password=%s' % (
            user, encrypted))
        return json_loads(answer)
