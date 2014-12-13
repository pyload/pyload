# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class FastixRu(Account):
    __name    = "FastixRu"
    __type    = "account"
    __version = "0.02"

    __description = """Fastix account plugin"""
    __license     = "GPLv3"
    __authors     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        page = json_loads(req.load("http://fastix.ru/api_v2/", get={'apikey': data['api'], 'sub': "getaccountdetails"}))

        points = page['points']
        kb     = float(points) * 1024 ** 2 / 1000

        if points > 0:
            account_info = {"validuntil": -1, "trafficleft": kb}
        else:
            account_info = {"validuntil": None, "trafficleft": None, "premium": False}
        return account_info


    def login(self, user, data, req):
        page = req.load("http://fastix.ru/api_v2/",
                        get={'sub': "get_apikey", 'email': user, 'password': data['password']})
        api = json_loads(page)
        api = api['apikey']
        data['api'] = api
        if "error_code" in page:
            self.wrongPassword()
