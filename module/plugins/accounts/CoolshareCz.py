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

#shares code with WarserverCz

from module.plugins.Account import Account
import re
from time import mktime, strptime

class CoolshareCz(Account):
    __name__ = "CoolshareCz"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """CoolShare.cz account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    VALID_UNTIL_PATTERN = ur'<li>Neomezené stahování do: <strong>(.+?)<'
    TRAFFIC_LEFT_PATTERN = ur'<li>Kredit: <strong>.*?\(\s*(.+?)\s*B\)'
    
    DOMAIN = "http://www.coolshare.cz"

    def loadAccountInfo(self, user, req):      
        html = req.load("%s/uzivatele/prehled" % self.DOMAIN, decode = True)
        
        validuntil = trafficleft = None
        premium = False
        
        found = re.search(self.VALID_UNTIL_PATTERN, html)
        if found:
            self.logDebug("VALID_UNTIL", found.group(1))
            try:                
                #validuntil = mktime(strptime(found.group(1), "%d %B %Y"))
                premium = True
                trafficleft = -1
            except Exception, e:
                self.logError(e)
                
        found = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if found:
            self.logDebug("TRAFFIC_LEFT", found.group(1))
            trafficleft = int(found.group(1).replace("&thinsp;","")) // 1024
            premium = True if trafficleft > 1 << 18 else False                           
        
        return ({"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium})
    
    def login(self, user, data, req):
        html = req.load('%s/uzivatele/prihlaseni?do=prihlaseni-submit' % self.DOMAIN, 
                        post = {"username": user,
                                "password": data['password'],
                                "send": u"Přihlásit"},
                        decode = True)
        
        if '<p class="chyba">' in html:          
            self.wrongPassword()