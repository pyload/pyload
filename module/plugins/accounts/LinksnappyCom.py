# -*- coding: utf-8 -*-

from hashlib import md5

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class LinksnappyCom(Account):
    __name__ = "LinksnappyCom"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """Linksnappy.com account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


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
            trafficleft = int(j['return']['trafficleft']) * 1024

        return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}

    def login(self, user, data, req):
        r = req.load('http://gen.linksnappy.com/lseAPI.php',
                     get={'act': 'USERDETAILS', 'username': user, 'password': md5(data['password']).hexdigest()})

        if 'Invalid Account Details' in r:
            self.wrongPassword()
