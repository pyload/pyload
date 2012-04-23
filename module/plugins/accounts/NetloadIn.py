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
from time import time

class NetloadIn(Account):
    __name__ = "NetloadIn"
    __version__ = "0.22"
    __type__ = "account"
    __description__ = """netload.in account plugin"""
    __author_name__ = ("RaNaN", "CryNickSystems")
    __author_mail__ = ("RaNaN@pyload.org", "webmaster@pcProfil.de")

    def loadAccountInfo(self, user, req):
        page = req.load("http://netload.in/index.php?id=2&lang=de")
        left = r">(\d+) (Tag|Tage), (\d+) Stunden<"
        left = re.search(left, page)
        if left:
            validuntil = time() + int(left.group(1)) * 24 * 60 * 60 + int(left.group(3)) * 60 * 60
            trafficleft = -1
            premium = True
        else:
            validuntil = None
            premium = False
            trafficleft = None
        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium" : premium}
    
    def login(self, user, data,req):
        page = req.load("http://netload.in/index.php", None, { "txtuser" : user, "txtpass" : data['password'], "txtcheck" : "login", "txtlogin" : "Login"}, cookies=True)
        if "password or it might be invalid!" in page:
            self.wrongPassword()
