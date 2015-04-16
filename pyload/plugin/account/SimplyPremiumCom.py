# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.Account import Account


class SimplyPremiumCom(Account):
    __name    = "SimplyPremiumCom"
    __type    = "account"
    __version = "0.05"

    __description = """Simply-Premium.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("EvolutionClip", "evolutionclip@live.de")]


    def loadAccountInfo(self, user, req):
        premium     = False
        validuntil  = -1
        trafficleft = None

        json_data = req.load('http://www.simply-premium.com/api/user.php?format=json')

        self.logDebug("JSON data: %s" % json_data)

        json_data = json_loads(json_data)

        if 'vip' in json_data['result'] and json_data['result']['vip']:
            premium = True

        if 'timeend' in json_data['result'] and json_data['result']['timeend']:
            validuntil = float(json_data['result']['timeend'])

        if 'remain_traffic' in json_data['result'] and json_data['result']['remain_traffic']:
            trafficleft = float(json_data['result']['remain_traffic'])

        return {"premium": premium, "validuntil": validuntil, "trafficleft": trafficleft}


    def login(self, user, data, req):
        req.cj.setCookie("simply-premium.com", "lang", "EN")

        html = req.load("http://www.simply-premium.com/login.php",
                        post={'key': user} if not data['password'] else {'login_name': user, 'login_pass': data['password']},
                        decode=True)

        if 'logout' not in html:
            self.wrongPassword()
