# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.Account import Account


class SimplyPremiumCom(Account):
    __name__    = "SimplyPremiumCom"
    __type__    = "account"
    __version__ = "0.04"

    __description__ = """Simply-Premium.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]


    def loadAccountInfo(self, user, req):
        validuntil  = -1
        trafficleft = None

        json_data = req.load('http://www.simply-premium.com/api/user.php?format=json')
        self.logDebug("JSON data: " + json_data)
        json_data = json_loads(json_data)

        if 'vip' in json_data['result'] and json_data['result']['vip'] == 0:
            return {"premium": False}

        if 'timeend' in json_data['result'] and json_data['result']['timeend']:
            validuntil = float(json_data['result']['timeend'])

        if 'remain_traffic' in json_data['result'] and json_data['result']['remain_traffic']:
            trafficleft = float(json_data['result']['remain_traffic']) / 1024  #@TODO: Remove `/ 1024` in 0.4.10

        return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}


    def login(self, user, data, req):
        req.cj.setCookie("simply-premium.com", "lang", "EN")

        if data['password'] == '' or data['password'] == '0':
            post_data = {"key": user}
        else:
            post_data = {"login_name": user, "login_pass": data['password']}

        html = req.load("http://www.simply-premium.com/login.php", post=post_data, decode=True)

        if 'logout' not in html:
            self.wrongPassword()
