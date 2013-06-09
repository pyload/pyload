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
    
    @author: zoidberg
"""

from module.plugins.Account import Account
import re
from time import mktime, strptime

class TurbobitNet(Account):
    __name__ = "TurbobitNet"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """TurbobitNet account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    #login_timeout = 60

    def loadAccountInfo(self, user, req):        
        html = req.load("http://turbobit.net")
           
        found = re.search(r'<u>Turbo Access</u> to ([0-9.]+)', html)
        if found:
            premium = True
            validuntil = mktime(strptime(found.group(1), "%d.%m.%Y"))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def login(self, user, data, req):
        req.cj.setCookie("turbobit.net", "user_lang", "en")
        
        html = req.load("http://turbobit.net/user/login", post={
            "user[login]": user,
            "user[pass]": data["password"],
            "user[submit]": "Login"})
        
        if not '<div class="menu-item user-name">' in html:
            self.wrongPassword()