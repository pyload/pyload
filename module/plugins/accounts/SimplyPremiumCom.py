# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.Account import Account


class SimplyPremiumCom(Account):
    __name__ = "SimplyPremiumCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Simply-Premium.com account plugin"""
    __author_name__ = "EvolutionClip"
    __author_mail__ = "evolutionclip@live.de"


    def loadAccountInfo(self, user, req):
        json_data = req.load('http://www.simply-premium.com/api/user.php?format=json')
        self.logDebug("JSON data: " + json_data)
        json_data = json_loads(json_data)

        if 'vip' in json_data['result'] and json_data['result']['vip'] == 0:
            return {"premium": False}

        #Time package
        validuntil = float(json_data['result']['timeend'])
        #Traffic package
        # {"trafficleft": int(traffic) / 1024, "validuntil": -1}
        #trafficleft = int(json_data['result']['traffic'] / 1024)

        #return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}
        return {"premium": True, "validuntil": validuntil}

    def login(self, user, data, req):
        req.cj.setCookie("simply-premium.com", "lang", "EN")

        if data['password'] == '' or data['password'] == '0':
            post_data = {"key": user}
        else:
            post_data = {"login_name": user, "login_pass": data['password']}

        html = req.load("http://www.simply-premium.com/login.php", post=post_data)

        if 'logout' not in html:
            self.wrongPassword()
