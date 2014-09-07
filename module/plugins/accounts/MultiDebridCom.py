# -*- coding: utf-8 -*-

from time import time

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class MultiDebridCom(Account):
    __name__ = "MultiDebridCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Multi-debrid.com account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


    def loadAccountInfo(self, user, req):
        if 'days_left' in self.json_data:
            validuntil = int(time() + self.json_data['days_left'] * 24 * 60 * 60)
            return {"premium": True, "validuntil": validuntil, "trafficleft": -1}
        else:
            self.logError('Unable to get account information')

    def login(self, user, data, req):
        # Password to use is the API-Password written in http://multi-debrid.com/myaccount
        html = req.load("http://multi-debrid.com/api.php",
                             get={"user": user, "pass": data['password']})
        self.logDebug('JSON data: ' + html)
        self.json_data = json_loads(html)
        if self.json_data['status'] != 'ok':
            self.logError('Invalid login. The password to use is the API-Password you find in your "My Account" page')
            self.wrongPassword()
