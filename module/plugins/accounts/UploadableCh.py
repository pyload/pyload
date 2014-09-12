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

    @author: sasch
"""

from module.plugins.Account import Account

class UploadableCh(Account):
    __name__ = "UploadableCh"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """Uploadable.ch account plugin"""
    __author_name__ = ("Sasch")

    def loadAccountInfo(self, user, req):
        page = req.load("http://www.uploadable.ch/login.php")
    
        if 'href="/premium.php">Upgrade to Premium' in page:
            return {"validuntil": -1, "trafficleft":-1, "premium": False}

      	if not '<a href="/logout.php"' in page:
            return {"validuntil": -1, "trafficleft": -1, "premium": False}
	
	return {"validultil": -1, "trafficleft": -1, "premium": True}


    def login(self, user, data, req):
        page = req.load('http://www.uploadable.ch/login.php', 
		post={ "userName" : user, "userPassword" : data["password"]
		, "autoLogin": "1", "action__login" :"normalLogin"}, cookies = True)
	
        if 'Login failed' in page:
            self.wrongPassword()
