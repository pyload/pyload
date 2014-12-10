# -*- coding: utf-8 -*-

from pyload.plugins.Account import Account
from pyload.utils import json_loads


class MegaDebridEu(Account):
    __name__    = "MegaDebridEu"
    __type__    = "account"
    __version__ = "0.20"

    __description__ = """mega-debrid.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("D.Ducatel", "dducatel@je-geek.fr")]


    # Define the base URL of MegaDebrid api
    API_URL = "https://www.mega-debrid.eu/api.php"


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        jsonResponse = req.load(self.API_URL,
                                get={'action': 'connectUser', 'login': user, 'password': data['password']})
        res = json_loads(jsonResponse)

        if res['response_code'] == "ok":
            return {"premium": True, "validuntil": float(res['vip_end']), "status": True}
        else:
            self.logError(res)
            return {"status": False, "premium": False}


    def login(self, user, data, req):
        jsonResponse = req.load(self.API_URL,
                                get={'action': 'connectUser', 'login': user, 'password': data['password']})
        res = json_loads(jsonResponse)
        if res['response_code'] != "ok":
            self.wrongPassword()
