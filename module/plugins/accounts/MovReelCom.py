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

    @author: t4skforce
"""

import re
from module.plugins.Account import Account
from module.plugins.internal.SimpleHoster import parseHtmlForm
from module.utils import parseFileSize


class MovReelCom(Account):
    __name__ = "MovReelCom"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Movreel.com account plugin"""
    __author_name__ = ("t4skforce")
    __author_mail__ = ("t4skforce1337[AT]gmail[DOT]com")
    
    #: after that time [in minutes] pyload will relogin the account
    login_timeout = 60
    #: account data will be reloaded after this time
    info_threshold = 30

    MAIN_PAGE = "http://movreel.com/"
    FREE_PATTERN = r'>Upgrade to premium<'
    TRAFFIC_PATTERN = r'Traffic.*?<b>([^<]+)</b>'
    
    def loadAccountInfo(self, user, req):
        html = req.load(self.MAIN_PAGE + '?op=my_account', decode=True)
        if 'User Login' in html:
            self.login(user, {"password":self.accounts[user]['password']}, req)
            
        account_info = {"validuntil": None, "trafficleft": None, "premium": False}
        
        isPremium = not re.search(self.FREE_PATTERN, html)
        if isPremium:
            account_info["premium"]=True
            account_info["trafficleft"]=-1
            
        traffic = re.search(self.TRAFFIC_PATTERN, html)
        if traffic:
            account_info["trafficleft"] = parseFileSize(traffic.group(1)) / 1024

        return account_info

    def login(self, user, data, req):
        html = req.load(self.MAIN_PAGE + 'login.html', decode=True)

        action, inputs = parseHtmlForm('name="FL"', html)
        if not inputs:
            inputs = {"op": "login", "redirect": self.MAIN_PAGE}

        inputs.update({"login": user, "password": data['password']})

        # Without this a 403 Forbidden is returned
        req.http.lastURL = self.MAIN_PAGE + 'login.html'
        html = req.load(self.MAIN_PAGE, post=inputs, decode=True)

        if 'Incorrect Login or Password' in html or '>Error<' in html:
            self.wrongPassword()