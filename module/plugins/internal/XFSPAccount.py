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

class XFSPAccount(Account):
    __name__ = "XFSPAccount"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """XFileSharingPro account base"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    MAIN_PAGE = None
    
    VALID_UNTIL_PATTERN = r'<TR><TD>Premium account expire:</TD><TD><b>([^<]+)</b>'
    TRAFFIC_LEFT_PATTERN = r'<TR><TD>Traffic available today:</TD><TD><b>(?P<S>[^<]+)</b>'   

    def loadAccountInfo(self, user, req):
        html = req.load(self.MAIN_PAGE + "?op=my_account", decode = True)
        
        validuntil = -1
        found = re.search(self.VALID_UNTIL_PATTERN, html)
        if found:
            premium = True
            try:
                self.logDebug(found.group(1))
                validuntil = mktime(strptime(found.group(1), "%d %B %Y"))
            except Exception, e:
                self.logError(e)
        else:
            premium = False
                    
        trafficleft = -1 
        
        return ({"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium})
    
    def login(self, user, data, req):
        html = req.load(self.MAIN_PAGE, post = {
            "login": user,
            "op": "login",
            "password": data['password'],
            "redirect": self.MAIN_PAGE
            }, decode = True)
        
        if 'Incorrect Login or Password' in html:          
            self.wrongPassword()