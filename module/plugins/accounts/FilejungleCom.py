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

class FilejungleCom(Account):
    __name__ = "FilejungleCom"
    __version__ = "0.11"
    __type__ = "account"
    __description__ = """filejungle.com account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    login_timeout = 60
    
    URL = "http://filejungle.com/"
    TRAFFIC_LEFT_PATTERN = r'"/extend_premium\.php">Until (\d+ [A-Za-z]+ \d+)<br'
    LOGIN_FAILED_PATTERN = r'<span htmlfor="loginUser(Name|Password)" generated="true" class="fail_info">'

    def loadAccountInfo(self, user, req):
        html = req.load(self.URL + "dashboard.php")
        found = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if found:
            premium = True
            validuntil = mktime(strptime(found.group(1), "%d %b %Y"))
        else:
            premium = False 
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def login(self, user, data, req):
        html = req.load(self.URL + "login.php", post={
            "loginUserName": user, 
            "loginUserPassword": data["password"],
            "loginFormSubmit": "Login",
            "recaptcha_challenge_field": "",	
            "recaptcha_response_field": "",	
            "recaptcha_shortencode_field": ""})
        
        if re.search(self.LOGIN_FAILED_PATTERN, html):
            self.wrongPassword()