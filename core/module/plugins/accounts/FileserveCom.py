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

class FileserveCom(Account):
    __name__ = "FileserveCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """fileserve.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def getAccountInfo(self, user):
        try:
            req = self.core.requestFactory.getRequest(self.__name__, user)
            
            src = req.load("http://fileserve.com/dashboard.php", cookies=True)
            
            out = Account.getAccountInfo(self, user)
            
            m = re.search(r"<td><h4>Premium Until</h4></th> <td><h5>(.*?) E(.)T</h5></td>", src)
            if m:
                zone = -5 if m.group(2) == "S" else -4
                validuntil = int(mktime(strptime(m.group(1), "%d %B %Y"))) + 24*3600 + (zone*3600)
                tmp = {"validuntil":validuntil, "trafficleft":-1}
            else:
                tmp = {"trafficleft":-1}
            out.update(tmp)
            return out
        except:
            return Account.getAccountInfo(user)
    
    def login(self, user, data):
        req = self.core.requestFactory.getRequest(self.__name__, user)
        req.load("http://fileserve.com/login.php",
                post={"loginUserName": user, "loginUserPassword": data["password"],
                      "autoLogin": "on", "loginFormSubmit": "Login"}, cookies=True)
        req.load("http://fileserve.com/dashboard.php", cookies=True)
        
