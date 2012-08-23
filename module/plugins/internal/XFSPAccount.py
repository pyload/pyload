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
from module.plugins.internal.SimpleHoster import parseHtmlForm
from module.utils import parseFileSize

class XFSPAccount(Account):
    __name__ = "XFSPAccount"
    __version__ = "0.05"
    __type__ = "account"
    __description__ = """XFileSharingPro account base"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    MAIN_PAGE = None
      
    VALID_UNTIL_PATTERN = r'>Premium account expire:</TD><TD><b>([^<]+)</b>'
    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:</TD><TD><b>([^<]+)</b>'
        
    def loadAccountInfo(self, user, req):      
        html = req.load(self.MAIN_PAGE + "?op=my_account", decode = True)
        
        validuntil = trafficleft = None
        premium = True if '>Renew premium<' in html else False
        
        found = re.search(self.VALID_UNTIL_PATTERN, html)
        if found:
            premium = True
            trafficleft = -1
            try:
                self.logDebug(found.group(1))
                validuntil = mktime(strptime(found.group(1), "%d %B %Y"))
            except Exception, e:
                self.logError(e)
        else:
            found = re.search(self.TRAFFIC_LEFT_PATTERN, html)
            if found:
                trafficleft = found.group(1)
                if "Unlimited" in trafficleft:
                    premium = True
                else:
                    trafficleft = parseFileSize(trafficleft) / 1024                            
        
        return ({"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium})
    
    def login(self, user, data, req):
        html = req.load('%slogin.html' % self.MAIN_PAGE, decode = True)
        
        action, inputs = parseHtmlForm('name="FL"', html)
        if not inputs:
            inputs = {"op": "login",
                      "redirect": self.MAIN_PAGE}        
        
        inputs.update({"login": user,
                       "password": data['password']})
        
        html = req.load(self.MAIN_PAGE, post = inputs, decode = True)
        
        if 'Incorrect Login or Password' in html or '>Error<' in html:          
            self.wrongPassword()