# -*- coding: utf-8 -*-

import hashlib
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


class SmoozedCom(Account):
    __name__    = "SmoozedCom"
    __type__    = "account"
    __version__ = "0.05"

    __description__ = """Smoozed.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("", "")]


    def loadAccountInfo(self, user, req):
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
                if float(status["data"]["user"].get("user_trial", 0)) > time.time():
                    info['premium'] = True
                else:
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
