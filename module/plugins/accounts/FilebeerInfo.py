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

import re
from time import mktime, strptime
from module.plugins.Account import Account
from module.utils import parseFileSize

class FilebeerInfo(Account):
    __name__ = "FilebeerInfo"
    __version__ = "0.02"
    __type__ = "account"
    __description__ = """filebeer.info account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    VALID_UNTIL_PATTERN = r'Reverts To Free Account:\s</td>\s*<td>\s*(.*?)\s*</td>'
    
    def loadAccountInfo(self, user, req):
        html = req.load("http://filebeer.info/upgrade.php", decode = True)        
        premium = not 'Free User </td>' in html
                
        validuntil = None
        if premium:
            try:
                validuntil = mktime(strptime(re.search(self.VALID_UNTIL_PATTERN, html).group(1), "%d/%m/%Y %H:%M:%S")) 
            except Exception, e:
                self.logError("Unable to parse account info", e)

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}
    
    def login(self, user, data, req):
        html = req.load('http://filebeer.info/login.php', post = {
            "submit": 'Login',
            "loginPassword": data['password'],
            "loginUsername": user,
            "submitme": '1'
            }, decode = True)
            
        if "<ul class='pageErrors'>" in html or ">Your username and password are invalid<" in html:
            self.wrongPassword()