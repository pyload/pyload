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

class FilefactoryCom(Account):
    __name__ = "FilefactoryCom"
    __version__ = "0.12"
    __type__ = "account"
    __description__ = """filefactory.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    ACCOUNT_INFO_PATTERN = r'<a href="/premium/">.*?datetime="(.*?)"'

    def loadAccountInfo(self, user, req):      
        html = req.load("http://www.filefactory.com/member/")
            
        found = re.search(self.ACCOUNT_INFO_PATTERN, html)
        if found:
            premium = True
            validuntil = mktime(strptime(re.sub(r"(\d)[a-z]{2} ", r"\1 ", found.group(1)),"%d %B, %Y"))
        else:
            premium = False
            validuntil = -1   

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def login(self, user, data, req):
        html = req.load("http://www.filefactory.com/member/login.php", post={
            "email": user, 
            "password": data["password"],
            "redirect": "/"})
            
        if '/member/login.php?err=1' in req.http.header:
            self.wrongPassword()
