# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: mkaay
"""

from time import mktime, strptime

from module.plugins.Account import Account
from module.common.json_layer import json_loads

class FileserveCom(Account):
    __name__ = "FileserveCom"
    __version__ = "0.2"
    __type__ = "account"
    __description__ = """fileserve.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")

    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)

        page = req.load("http://app.fileserve.com/api/login/", post={"username": user, "password": data["password"],
                                                                     "submit": "Submit+Query"})
        res = json_loads(page)

        if res["type"] == "premium":
            validuntil = mktime(strptime(res["expireTime"], "%Y-%m-%d %H:%M:%S"))
            return {"trafficleft": res["traffic"], "validuntil": validuntil}
        else:
            return {"premium": False, "trafficleft": None, "validuntil": None}


    def login(self, user, data, req):
        page = req.load("http://app.fileserve.com/api/login/", post={"username": user, "password": data["password"],
                                                                     "submit": "Submit+Query"})
        res = json_loads(page)

        if not res["type"]:
            self.wrongPassword()

        #login at fileserv page
        req.load("http://www.fileserve.com/login.php",
                 post={"loginUserName": user, "loginUserPassword": data["password"], "autoLogin": "checked",
                       "loginFormSubmit": "Login"})
