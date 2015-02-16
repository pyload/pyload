# -*- coding: utf-8 -*-

from time import mktime, strptime

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class FileserveCom(Account):
    __name    = "FileserveCom"
    __type    = "account"
    __version = "0.20"

    __description = """Fileserve.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)

        html = req.load("http://app.fileserve.com/api/login/", post={"username": user, "password": data['password'],
                                                                     "submit": "Submit+Query"})
        res = json_loads(html)

        if res['type'] == "premium":
            validuntil = mktime(strptime(res['expireTime'], "%Y-%m-%d %H:%M:%S"))
            return {"trafficleft": res['traffic'], "validuntil": validuntil}
        else:
            return {"premium": False, "trafficleft": None, "validuntil": None}


    def login(self, user, data, req):
        html = req.load("http://app.fileserve.com/api/login/", post={"username": user, "password": data['password'],
                                                                     "submit": "Submit+Query"})
        res = json_loads(html)

        if not res['type']:
            self.wrongPassword()

        #login at fileserv html
        req.load("http://www.fileserve.com/login.php",
                 post={"loginUserName": user, "loginUserPassword": data['password'], "autoLogin": "checked",
                       "loginFormSubmit": "Login"})
