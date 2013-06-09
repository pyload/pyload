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
from module.plugins.Account import Account
from module.utils import parseFileSize
from module.common.json_layer import json_loads

class RapidgatorNet(Account):
    __name__ = "RapidgatorNet"
    __version__ = "0.04"
    __type__ = "account"
    __description__ = """rapidgator.net account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    API_URL = 'http://rapidgator.net/api/user'
        
    def loadAccountInfo(self, user, req):
        try:
            sid = self.getAccountData(user).get('SID') 
            assert sid
            
            json = req.load("%s/info?sid=%s" % (self.API_URL, sid))
            self.logDebug("API:USERINFO", json)            
            json = json_loads(json)
                        
            if json['response_status'] == 200:
                if "reset_in" in json['response']:
                    self.scheduleRefresh(user, json['response']['reset_in'])
                                                    
                return {"validuntil": json['response']['expire_date'], 
                        "trafficleft": int(json['response']['traffic_left']) / 1024, 
                        "premium": True}
            else:
                self.logError(json['response_details'])
        except Exception, e:
            self.logError(e)

        return {"validuntil": None, "trafficleft": None, "premium": False}
    
    def login(self, user, data, req):                              
        try:
            json = req.load('%s/login' % self.API_URL, 
                post = {"username": user,
                        "password": data['password']})            
            self.logDebug("API:LOGIN", json)
            json = json_loads(json)            
        
            if json['response_status'] == 200:
                data['SID'] = str(json['response']['session_id'])
                return            
            else:
                self.logError(json['response_details'])
        except Exception, e:
            self.logError(e)
            
        self.wrongPassword()
