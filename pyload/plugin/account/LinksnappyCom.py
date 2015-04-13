# -*- coding: utf-8 -*-

from hashlib import md5

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class LinksnappyCom(Account):
    __name    = "LinksnappyCom"
    __type    = "account"
    __version = "0.05"
    __description = """Linksnappy.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        r = req.load('http://gen.linksnappy.com/lseAPI.php',
                     get={'act': 'USERDETAILS', 'username': user, 'password': md5(data['password']).hexdigest()})

        self.logDebug("JSON data: " + r)

        j = json_loads(r)

        if j['error']:
            return {"premium": False}

        validuntil = j['return']['expire']

        if validuntil == 'lifetime':
            validuntil = -1

        elif validuntil == 'expired':
            return {"premium": False}

        else:
            validuntil = float(validuntil)

        if 'trafficleft' not in j['return'] or isinstance(j['return']['trafficleft'], str):
            trafficleft = -1
        else:
            trafficleft = self.parseTraffic("%d MB" % j['return']['trafficleft'])

        return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}


    def login(self, user, data, req):
        r = req.load("http://gen.linksnappy.com/lseAPI.php",
                     get={'act'     : 'USERDETAILS',
                          'username': user,
                          'password': md5(data['password']).hexdigest()},
                     decode=True)

        if 'Invalid Account Details' in r:
            self.wrongPassword()
