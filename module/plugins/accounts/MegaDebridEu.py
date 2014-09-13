# -*- coding: utf-8 -*-

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class MegaDebridEu(Account):
    __name__ = "MegaDebridEu"
    __type__ = "account"
    __version__ = "0.2"

    __description__ = """mega-debrid.eu account plugin"""
    __author_name__ = "D.Ducatel"
    __author_mail__ = "dducatel@je-geek.fr"

    # Define the base URL of MegaDebrid api
    API_URL = "https://www.mega-debrid.eu/api.php"


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        jsonResponse = req.load(self.API_URL,
                                get={'action': 'connectUser', 'login': user, 'password': data['password']})
        response = json_loads(jsonResponse)

        if response['response_code'] == "ok":
            return {"premium": True, "validuntil": float(response['vip_end']), "status": True}
        else:
            self.logError(response)
            return {"status": False, "premium": False}

    def login(self, user, data, req):
        jsonResponse = req.load(self.API_URL,
                                get={'action': 'connectUser', 'login': user, 'password': data['password']})
        response = json_loads(jsonResponse)
        if response['response_code'] != "ok":
            self.wrongPassword()
