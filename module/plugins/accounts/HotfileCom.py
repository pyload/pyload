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
import re
from time import strptime, mktime
import hashlib

class HotfileCom(Account):
    __name__ = "HotfileCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """hotfile.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def getAccountInfo(self, user):
        req = self.core.requestFactory.getRequest(self.__name__, user)
        
        resp = self.apiCall("getuserinfo", user=user)
        if resp.startswith("."):
            self.core.debug("HotfileCom API Error: %s" % resp)
            return None
        info = {}
        for p in resp.split("&"):
            key, value = p.split("=")
            info[key] = value
            
        info["premium_until"] = info["premium_until"].replace("T"," ")
        zone = info["premium_until"][19:]
        info["premium_until"] = info["premium_until"][:19]
        zone = int(zone[:3])
        
        validuntil = int(mktime(strptime(info["premium_until"], "%Y-%m-%d %H:%M:%S"))) + (zone*3600)
        out = Account.getAccountInfo(self, user)
        tmp = {"validuntil":validuntil, "trafficleft":-1}
        out.update(tmp)
        return out
    
    def apiCall(self, method, post={}, user=None):
        if user:
            data = None
            for account in self.accounts.items():
                if account[0] == user:
                    data = account[1]
        else:
            user, data = self.accounts.items()[0]
        
        req = self.core.requestFactory.getRequest(self.__name__, user)
    
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
        return req.load("http://api.hotfile.com/", post=post)
    
    def login(self, user, data):
        req = self.core.requestFactory.getRequest(self.__name__, user)
        cj = self.core.requestFactory.getCookieJar(self.__name__, user)
        cj.setCookie("hotfile.com", "lang", "en")
        req.load("http://hotfile.com/", cookies=True)
        req.load("http://hotfile.com/login.php", post={"returnto": "/", "user": user, "pass": data["password"]}, cookies=True)
