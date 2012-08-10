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
from module.plugins.internal.SimpleHoster import parseHtmlForm
import re
from module.utils import parseFileSize
from time import mktime, strptime

class EasybytezCom(Account):
    __name__ = "EasybytezCom"
    __version__ = "0.02"
    __type__ = "account"
    __description__ = """EasyBytez.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    VALID_UNTIL_PATTERN = r'<TR><TD>Premium account expire:</TD><TD><b>([^<]+)</b>'
    TRAFFIC_LEFT_PATTERN = r'<TR><TD>Traffic available today:</TD><TD><b>(?P<S>[^<]+)</b>'

    def loadAccountInfo(self, user, req):      
        html = req.load("http://www.easybytez.com/?op=my_account", decode = True)
        
        validuntil = trafficleft = None
        premium = False
        
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
        html = req.load('http://www.easybytez.com/login.html', decode = True)
        action, inputs = parseHtmlForm('name="FL"', html)
        inputs.update({"login": user,
                       "password": data['password'],
                       "redirect": "http://www.easybytez.com/"})
        
        html = req.load(action, post = inputs, decode = True)
        
        if 'Incorrect Login or Password' in html or '>Error<' in html:          
            self.wrongPassword()