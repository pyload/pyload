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
from time import strptime, mktime
import hashlib

class HotfileCom(Account):
    __name__ = "HotfileCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """hotfile.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def loadAccountInfo(self, user, req):
        resp = self.apiCall("getuserinfo", user=user)
        if resp.startswith("."):
            self.core.debug("HotfileCom API Error: %s" % resp)
            raise Exception
        info = {}
        for p in resp.split("&"):
            key, value = p.split("=")
            info[key] = value

        info["premium_until"] = info["premium_until"].replace("T"," ")
        zone = info["premium_until"][19:]
        info["premium_until"] = info["premium_until"][:19]
        zone = int(zone[:3])

        validuntil = int(mktime(strptime(info["premium_until"], "%Y-%m-%d %H:%M:%S"))) + (zone*3600)

        tmp = {"validuntil":validuntil, "trafficleft":-1}
        return tmp
    
    def apiCall(self, method, post={}, user=None):
        if user:
            data = self.getAccountData(user)
        else:
            user, data = self.selectAccount()
        
        req = self.getAccountRequest(user)
    
        digest = req.load("http://api.hotfile.com/", post={"action":"getdigest"})
        h = hashlib.md5()
        h.update(data["password"])
        hp = h.hexdigest()
        h = hashlib.md5()
        h.update(hp)
        h.update(digest)
        pwhash = h.hexdigest()
        
        post.update({"action": method})
        post.update({"username":user, "passwordmd5dig":pwhash, "digest":digest})
        resp = req.load("http://api.hotfile.com/", post=post)
        req.close()
        return resp
    
    def login(self, user, data, req):
        cj = self.getAccountCookies(user)
        cj.setCookie("hotfile.com", "lang", "en")
        req.load("http://hotfile.com/", cookies=True)
        page = req.load("http://hotfile.com/login.php", post={"returnto": "/", "user": user, "pass": data["password"]}, cookies=True)

        if "Bad username/password" in page:
            self.wrongPassword()
