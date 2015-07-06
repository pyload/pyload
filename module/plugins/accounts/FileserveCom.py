# -*- coding: utf-8 -*-

import time

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class FileserveCom(Account):
    __name__    = "FileserveCom"
    __type__    = "account"
    __version__ = "0.22"

    __description__ = """Fileserve.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


    def load_account_info(self, user, req):
        data = self.get_account_data(user)

        html = self.load("http://app.fileserve.com/api/login/", post={"username": user, "password": data['password'],
                                                                     "submit": "Submit+Query"}, req=req)
        res = json_loads(html)

        if res['type'] == "premium":
            validuntil = time.mktime(time.strptime(res['expireTime'], "%Y-%m-%d %H:%M:%S"))
            return {"trafficleft": res['traffic'], "validuntil": validuntil}
        else:
            return {"premium": False, "trafficleft": None, "validuntil": None}


    def login(self, user, data, req):
        html = self.load("http://app.fileserve.com/api/login/", post={"username": user, "password": data['password'],
                                                                     "submit": "Submit+Query"}, req=req)
        res = json_loads(html)

        if not res['type']:
            self.wrong_password()

        # login at fileserv html
        self.load("http://www.fileserve.com/login.php",
                 post={"loginUserName": user, "loginUserPassword": data['password'], "autoLogin": "checked",
                       "loginFormSubmit": "Login"}, req=req)
