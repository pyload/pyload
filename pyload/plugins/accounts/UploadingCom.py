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
from time import time, strptime, mktime
import re

class UploadingCom(Account):
    __name__ = "UploadingCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """uploading.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def loadAccountInfo(self, user, req):
        src = req.load("http://uploading.com/")
        premium = True
        if "UPGRADE TO PREMIUM" in src:
            return {"validuntil": -1, "trafficleft": -1, "premium": False}
        
        m = re.search("Valid Until:(.*?)<", src)
        if m:
            validuntil = int(mktime(strptime(m.group(1).strip(), "%b %d, %Y")))
        else:
            validuntil = -1
        
        return {"validuntil": validuntil, "trafficleft": -1, "premium": True}
        
    def login(self, user, data, req):
        req.cj.setCookie("uploading.com", "lang", "1")
        req.cj.setCookie("uploading.com", "language", "1")
        req.cj.setCookie("uploading.com", "setlang", "en")
        req.cj.setCookie("uploading.com", "_lang", "en")
        req.load("http://uploading.com/")
        req.load("http://uploading.com/general/login_form/?JsHttpRequest=%s-xml" % long(time()*1000), post={"email": user, "password": data["password"], "remember": "on"})
