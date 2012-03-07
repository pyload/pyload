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
import re
from time import time, mktime, strptime

class BayfilesCom(Account):
    __name__ = "BayfilesCom"
    __version__ = "0.02"
    __type__ = "account"
    __description__ = """bayfiles.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    def loadAccountInfo(self, user, req):
        for i in range(2):
            response = json_loads(req.load("http://api.bayfiles.com/v1/account/info"))
            self.logDebug(response)            
            if not response["error"]: 
                break
            self.logWarning(response["error"])
            self.relogin()
        
        return {"premium": bool(response['premium']), \
                "trafficleft": -1, \
                "validuntil": response['expires'] if response['expires'] >= int(time()) else -1}

    def login(self, user, data, req):
        response = json_loads(req.load("http://api.bayfiles.com/v1/account/login/%s/%s" % (user, data["password"])))
        self.logDebug(response)
        if response["error"]:
            self.logError(response["error"])
            self.wrongPassword()