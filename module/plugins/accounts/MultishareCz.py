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
#from time import mktime, strptime
#from pycurl import REFERER
import re
from module.utils import parseFileSize

class MultishareCz(Account):
    __name__ = "MultishareCz"
    __version__ = "0.02"
    __type__ = "account"
    __description__ = """multishare.cz account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    TRAFFIC_LEFT_PATTERN = r'<span class="profil-zvyrazneni">Kredit:</span>\s*<strong>(?P<S>[0-9,]+)&nbsp;(?P<U>\w+)</strong>'
    ACCOUNT_INFO_PATTERN = r'<input type="hidden" id="(u_ID|u_hash)" name="[^"]*" value="([^"]+)">'

    def loadAccountInfo(self, user, req):
        #self.relogin(user)
        html = req.load("http://www.multishare.cz/profil/", decode = True)
                    
        found = re.search(self.TRAFFIC_LEFT_PATTERN, html)           
        trafficleft = parseFileSize(found.group('S'), found.group('U')) / 1024 if found else 0
        self.premium = True if trafficleft else False 
        
        html = req.load("http://www.multishare.cz/", decode = True)
        mms_info = dict(re.findall(self.ACCOUNT_INFO_PATTERN, html))

        return dict(mms_info, **{"validuntil": -1, "trafficleft": trafficleft})
    
    def login(self, user, data, req):
        html = req.load('http://www.multishare.cz/html/prihlaseni_process.php', post = {
            "akce":	"Přihlásit",
            "heslo": data['password'],
            "jmeno": user
            }, decode = True)
        
        if '<div class="akce-chyba akce">' in html:
            self.wrongPassword()