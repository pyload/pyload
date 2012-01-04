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

import re
from time import time

from module.plugins.Account import Account

class MegauploadCom(Account):
    __name__ = "MegauploadCom"
    __version__ = "0.12"
    __type__ = "account"
    __description__ = """megaupload account plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")
    
    def loadAccountInfo(self, user, req):
        page = req.load("http://www.megaupload.com/?c=account&setlang=en", decode = True)
        
        premium = False if r'<div class="account_txt">Regular' in page else True
        validuntil = -1
        
        if premium:
            found = re.search(r'class="account_txt">\s*(\d+)\s*(days|hours|minutes) remaining', page)
            if found:
                validuntil = time() + 60 * int(found.group(1)) * {"days": 1440, "hours": 60, "minutes": 1}[found.group(2)]             
    
            if '<div class="account_txt" id="ddltxt"> Deactivated </div>' in page:
                self.core.log.warning(_("Activate direct Download in your MegaUpload Account"))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}


    def login(self, user, data, req):
        page = req.load("http://www.megaupload.com/?c=login&next=c%3Dpremium", post={ "username" : user, "password" : data["password"], "login" :"1"}, cookies=True)
        if "Username and password do not match" in page:
            self.wrongPassword()
