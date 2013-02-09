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

from module.plugins.Account import Account

class ShareonlineBiz(Account):
    __name__ = "ShareonlineBiz"
    __version__ = "0.24"
    __type__ = "account"
    __description__ = """share-online.biz account plugin"""
    __author_name__ = ("mkaay", "zoidberg")
    __author_mail__ = ("mkaay@mkaay.de", "zoidberg@mujmail.cz")

    def getUserAPI(self, user, req):
        return req.load("http://api.share-online.biz/account.php",
            {"username": user, "password": self.accounts[user]["password"], "act": "userDetails"})

    def loadAccountInfo(self, user, req):
        src = self.getUserAPI(user, req)

        info = {}
        for line in src.splitlines():
            if "=" in line:
                key, value = line.split("=")
                info[key] = value
        self.logDebug(info)

        if "dl" in info and info["dl"].lower() != "not_available":
            req.cj.setCookie("share-online.biz", "dl", info["dl"])
        if "a" in info and info["a"].lower() != "not_available":
            req.cj.setCookie("share-online.biz", "a", info["a"])

        return {"validuntil": int(info["expire_date"]) if "expire_date" in info else -1,
                "trafficleft": -1,
                "premium": True if ("dl" in info or "a" in info) and (info["group"] != "Sammler") else False}

    def login(self, user, data, req):
        src = self.getUserAPI(user, req)
        if "EXCEPTION" in src:
            self.wrongPassword()