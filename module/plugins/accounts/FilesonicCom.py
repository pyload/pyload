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

    @author: RaNaN
"""

from time import mktime, strptime

from module.plugins.Account import Account
from module.common.json_layer import json_loads

class FilesonicCom(Account):
    __name__ = "FilesonicCom"
    __version__ = "0.31"
    __type__ = "account"
    __description__ = """filesonic.com account plugin"""
    __author_name__ = ("RaNaN", "Paul King")
    __author_mail__ = ("RaNaN@pyload.org", "")

    API_URL = "http://api.filesonic.com"

    def getDomain(self, req):
        xml = req.load(self.API_URL + "/utility?method=getFilesonicDomainForCurrentIp&format=json",
                       decode=True)
        return json_loads(xml)["FSApi_Utility"]["getFilesonicDomainForCurrentIp"]["response"]

    def loadAccountInfo(self, req):
        xml = req.load(self.API_URL + "/user?method=getInfo&format=json",
                       post={"u": self.loginname,
                             "p": self.password}, decode=True)

        self.logDebug("account status retrieved from api %s" % xml)

        json = json_loads(xml)
        if json["FSApi_User"]["getInfo"]["status"] != "success":
            self.logError(_("Invalid login retrieving user details"))
            return {"validuntil": -1, "trafficleft": -1, "premium": False}
        premium = json["FSApi_User"]["getInfo"]["response"]["users"]["user"]["is_premium"]
        if premium:
            validuntil = json["FSApi_User"]["getInfo"]["response"]["users"]["user"]["premium_expiration"]
            validuntil = int(mktime(strptime(validuntil, "%Y-%m-%d %H:%M:%S")))
        else:
            validuntil = -1
        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def login(self, req):
        domain = self.getDomain(req)

        post_vars = {
            "email": self.loginname,
            "password": self.password,
            "rememberMe": 1
        }
        page = req.load("http://www%s/user/login" % domain, cookies=True, post=post_vars, decode=True)

        if "Provided password does not match." in page or "You must be logged in to view this page." in page:
            self.wrongPassword()

