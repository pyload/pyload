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

import re
from time import strptime, mktime

from module.plugins.Account import Account

class ShareCx(Account):
    __name__ = "ShareCx"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """share.cx account plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def loadAccountInfo(self, user, req):
        page = req.load("http://www.share.cx/myaccount")

        valid = re.search("<TR><TD>Valid till</TD><TD>([0-9\.]+)</TD></TR>", page, re.IGNORECASE).group(1)
        valid = int(mktime(strptime(valid, "%d.%m.%Y")))

        return {"trafficleft": -1, "validuntil" : valid}

    
    def login(self, user, data,req):
        req.cj.setCookie("share.cx", "lang", "english")
        page = req.load("http://www.share.cx", None, { "redirect" : "http://www.share.cx/", "login": user, "password" : data['password'], "op" : "login"})

        if "Incorrect Login or Password" in page:
            self.wrongPassword()