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

class YibaishiwuCom(Account):
    __name__ = "YibaishiwuCom"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """115.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    ACCOUNT_INFO_PATTERN = r'var USER_PERMISSION = {(.*?)}'

    def loadAccountInfo(self, user, req):
        #self.relogin(user)
        html = req.load("http://115.com/", decode = True)
        
        found = re.search(self.ACCOUNT_INFO_PATTERN, html, re.S)
        premium = True if (found and 'is_vip: 1' in found.group(1)) else False
        validuntil = trafficleft = (-1 if found else 0)
        return dict({"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium})

    def login(self, user, data, req):
        html = req.load('http://passport.115.com/?ac=login', post = {
            "back": "http://www.115.com/",
            "goto": "http://115.com/",
            "login[account]": user,
            "login[passwd]": data['password']
            }, decode = True)

        if not 'var USER_PERMISSION = {' in html:
            self.wrongPassword()