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
import re

class ShareonlineBiz(Account):
    __name__ = "ShareonlineBiz"
    __version__ = "0.2"
    __type__ = "account"
    __description__ = """share-online.biz account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def getAccountInfo(self, user):
        req = self.core.requestFactory.getRequest(self.__name__, user)
        src = req.load("https://www.share-online.biz/alpha/user/profile")
        
        validuntil = re.search(r"Account gültig bis:.*?<span class='.*?'>(.*?)</span>", src).group(1)
        validuntil = int(mktime(strptime(validuntil, "%m/%d/%Y, %I:%M:%S %p")))
        
        out = Account.getAccountInfo(self, user)
        tmp = {"validuntil":validuntil, "trafficleft":-1}
        out.update(tmp)
        return out
    
    def login(self, user, data):
        req = self.core.requestFactory.getRequest(self.__name__, user)
        post_vars = {"user": user,
                        "pass": data["password"],
                        "l_rememberme":"1"}
        req.lastURL = "http://www.share-online.biz/alpha/"
        req.load("https://www.share-online.biz/alpha/user/login", cookies=True, post=post_vars)
