# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class MegaDebridEu(Account):
    __name__    = "MegaDebridEu"
    __type__    = "account"
    __version__ = "0.22"

    __description__ = """Mega-debrid.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("D.Ducatel", "dducatel@je-geek.fr")]


    #: Define the base URL of MegaDebrid api
    API_URL = "https://www.mega-debrid.eu/api.php"


    def load_account_info(self, user, req):
        data = self.get_account_data(user)
        jsonResponse = self.load(self.API_URL,
                                 get={'action'  : 'connectUser',
                                      'login'   : user,
                                      'password': data['password']},
                                 req=req)
        res = json_loads(jsonResponse)

        if res['response_code'] == "ok":
            return {"premium": True, "validuntil": float(res['vip_end']), "status": True}
        else:
            self.log_error(res)
            return {"status": False, "premium": False}


    def login(self, user, data, req):
        jsonResponse = self.load(self.API_URL,
                                 get={'action'  : 'connectUser',
                                      'login'   : user,
                                      'password': data['password']},
                                 req=req)
        res = json_loads(jsonResponse)
        if res['response_code'] != "ok":
            self.wrong_password()
