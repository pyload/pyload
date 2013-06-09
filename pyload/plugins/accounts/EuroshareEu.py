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
from time import mktime, strptime
from string import replace
import re

class EuroshareEu(Account):
    __name__ = "EuroshareEu"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """euroshare.eu account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    def loadAccountInfo(self, user, req):
        self.relogin(user)
        html = req.load("http://euroshare.eu/customer-zone/settings/")
        
        found = re.search('id="input_expire_date" value="(\d+\.\d+\.\d+ \d+:\d+)"', html)
        if found is None:
            premium, validuntil = False, -1
        else:
            premium = True
            validuntil = mktime(strptime(found.group(1), "%d.%m.%Y %H:%M"))
        
        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}
    
    def login(self, user, data, req):
    
        html = req.load('http://euroshare.eu/customer-zone/login/', post={
                "trvale": "1",
                "login": user,
                "password": data["password"]
                }, decode=True)
                
        if u">Nesprávne prihlasovacie meno alebo heslo" in html:
            self.wrongPassword()