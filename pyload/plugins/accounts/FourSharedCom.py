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
from module.common.json_layer import json_loads

class FourSharedCom(Account):
    __name__ = "FourSharedCom"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """FourSharedCom account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    def loadAccountInfo(self, user, req):                           
        #fixme
        return ({"validuntil": -1, "trafficleft": -1, "premium": False})
    
    def login(self, user, data, req):
        req.cj.setCookie("www.4shared.com", "4langcookie", "en")
        response = req.load('http://www.4shared.com/login',
                            post = {"login": user,
                                    "password": data['password'],
                                    "remember": "false",
                                    "doNotRedirect": "true"})
        self.logDebug(response) 
        response = json_loads(response)
        
        if not "ok" in response or response['ok'] != True:
            if "rejectReason" in response and response['rejectReason'] != True:
                self.logError(response['rejectReason'])      
            self.wrongPassword()