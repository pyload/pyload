# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.Account import Account


class HighWayMe(Account):
    __name__    = "HighWayMe.py"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """High-Way.Me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]


    def loadAccountInfo(self, user, req):
        premium     = False
        validuntil  = -1
        trafficleft = None

        json_data = req.load('https://high-way.me/api.php?user')

        self.logDebug("JSON data: %s" % json_data)

        json_data = json_loads(json_data)

        if 'premium' in json_data['user'] and json_data['user']['premium']:
            premium = True

        if 'premium_bis' in json_data['user'] and json_data['user']['premium_bis']:
            validuntil = float(json_data['user']['premium_bis'])

        if 'premium_traffic' in json_data['user'] and json_data['user']['premium_traffic']:
            trafficleft = float(json_data['user']['premium_traffic']) / 1024  #@TODO: Remove `/ 1024` in 0.4.10

        return {"premium": premium, "validuntil": validuntil, "trafficleft": trafficleft}


    def login(self, user, data, req):

        html = req.load("https://high-way.me/api.php?login",
                        post={'login': '1', 'user': user, 'pass': data['password']},
                        decode=True)

        if 'UserOrPassInvalid' in html:
            self.wrongPassword()
