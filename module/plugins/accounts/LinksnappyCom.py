# -*- coding: utf-8 -*-

import hashlib

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class LinksnappyCom(Account):
    __name__    = "LinksnappyCom"
    __type__    = "account"
    __version__ = "0.07"
    __status__  = "testing"

    __description__ = """Linksnappy.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def parse_info(self, user, password, data, req):
        data = self.get_data(user)
        r = self.load('http://gen.linksnappy.com/lseAPI.php',
                      get={'act'     : 'USERDETAILS',
                           'username': user,
                           'password': hashlib.md5(password).hexdigest()})

        self.log_debug("JSON data: " + r)

        j = json_loads(r)

        if j['error']:
            return {'premium': False}

        validuntil = j['return']['expire']

        if validuntil == "lifetime":
            validuntil = -1

        elif validuntil == "expired":
            return {'premium': False}

        else:
            validuntil = float(validuntil)

        if 'trafficleft' not in j['return'] or isinstance(j['return']['trafficleft'], str):
            trafficleft = -1
        else:
            trafficleft = self.parse_traffic("%d MB" % j['return']['trafficleft'])

        return {'premium'    : True       ,
                'validuntil' : validuntil ,
                'trafficleft': trafficleft}


    def login(self, user, password, data, req):
        html = self.load("https://gen.linksnappy.com/lseAPI.php",
                         get={'act'     : 'USERDETAILS',
                              'username': user,
                              'password': hashlib.md5(password).hexdigest()})

        if "Invalid Account Details" in html:
            self.login_fail()
