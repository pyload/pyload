# -*- coding: utf-8 -*-

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

from module.plugins.internal.misc import json
from module.plugins.internal.Account import Account


class OboomCom(Account):
    __name__    = "OboomCom"
    __type__    = "account"
    __version__ = "0.31"
    __status__  = "testing"

    __description__ = """Oboom.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stanley", "stanley.foerster@gmail.com")]


    def load_account_data(self, user, password):
        salt   = password[::-1]
        pbkdf2 = PBKDF2(password, salt, 1000).hexread(16)

        html = self.load("http://www.oboom.com/1/login",  #@TODO: Revert to `https` in 0.4.10
                         get={'auth': user,
                              'pass': pbkdf2})
        result = json.loads(html)

        if result[0] != 200:
            self.log_warning(_("Failed to log in: %s") % result[1])
            self.fail_login()

        return result[1]


    def grab_info(self, user, password, data):
        account_data = self.load_account_data(user, password)

        userData = account_data['user']

        premium = userData['premium'] != "null"

        if userData['premium_unix'] == "null":
            validUntil = -1
        else:
            validUntil = float(userData['premium_unix'])

        traffic = userData['traffic']

        trafficLeft = traffic['current'] / 1024  #@TODO: Remove `/ 1024` in 0.4.10
        maxTraffic  = traffic['max'] / 1024  #@TODO: Remove `/ 1024` in 0.4.10

        session = account_data['session']

        return {'premium'    : premium,
                'validuntil' : validUntil,
                'trafficleft': trafficLeft,
                'maxtraffic' : maxTraffic,
                'session'    : session}


    def signin(self, user, password, data):
        self.load_account_data(user, password)
