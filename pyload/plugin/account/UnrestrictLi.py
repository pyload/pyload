# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class UnrestrictLi(Account):
    __name    = "UnrestrictLi"
    __type    = "account"
    __version = "0.03"

    __description = """Unrestrict.li account plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def loadAccountInfo(self, user, req):
        json_data = req.load('http://unrestrict.li/api/jdownloader/user.php?format=json')
        self.logDebug("JSON data: " + json_data)
        json_data = json_loads(json_data)

        if 'vip' in json_data['result'] and json_data['result']['vip'] == 0:
            return {"premium": False}

        validuntil = json_data['result']['expires']
        trafficleft = int(json_data['result']['traffic'])

        return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}


    def login(self, user, data, req):
        req.cj.setCookie("unrestrict.li", "lang", "EN")
        html = req.load("https://unrestrict.li/sign_in")

        if 'solvemedia' in html:
            self.logError(_("A Captcha is required. Go to http://unrestrict.li/sign_in and login, then retry"))
            return

        post_data = {"username": user, "password": data['password'],
                     "remember_me": "remember", "signin": "Sign in"}
        html = req.load("https://unrestrict.li/sign_in", post=post_data)

        if 'sign_out' not in html:
            self.wrongPassword()
