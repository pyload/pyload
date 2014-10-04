# -*- coding: utf-8 -*-

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class FastixRu(Account):
    __name__ = "FastixRu"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """Fastix account plugin"""
    __author_name__ = "Massimo Rosamilia"
    __author_mail__ = "max@spiritix.eu"


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        page = req.load("http://fastix.ru/api_v2/?apikey=%s&sub=getaccountdetails" % (data['api']))
        page = json_loads(page)
        points = page['points']
        kb = float(points)
        kb = kb * 1024 ** 2 / 1000
        if points > 0:
            account_info = {"validuntil": -1, "trafficleft": kb}
        else:
            account_info = {"validuntil": None, "trafficleft": None, "premium": False}
        return account_info

    def login(self, user, data, req):
        page = req.load("http://fastix.ru/api_v2/?sub=get_apikey&email=%s&password=%s" % (user, data['password']))
        api = json_loads(page)
        api = api['apikey']
        data['api'] = api
        if "error_code" in page:
            self.wrongPassword()
