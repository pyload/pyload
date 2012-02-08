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
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """filefactory.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    ACCOUNT_INFO_PATTERN = r'Your account is valid until the <strong>(.*?)</strong>' 

    def loadAccountInfo(self, user, req):
        premium = False
        validuntil = -1
        
        html = req.load("http://filefactory.com/member/")
        if "You are a FileFactory Premium Member" in html:
            premium = True
            found = re.search(self.ACCOUNT_INFO_PATTERN, html)
            if found:
                validuntil = mktime(strptime(re.sub(r"(\d)[a-z]{2} ", r"\1 ", found.group(1)),"%d %B, %Y")) 

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def login(self, user, data, req):
        html = req.load("http://filefactory.com/member/login.php", post={
            "email": user, 
            "password": data["password"],
            "redirect": "/"})
            
        if not re.search(r'location:.*?\?login=1', req.http.header, re.I):
            self.wrongPassword()