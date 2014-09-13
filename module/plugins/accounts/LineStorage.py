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

    @author: gsasch
"""

from module.plugins.Account import Account

class LineStorage(Account):
    __name__ = "LineStorage"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """LineStorage account plugin"""
    __author_name__ = ("gsasch")

    def loadAccountInfo(self, user, req):
        page = req.load("http://linestorage.com")
    
        if '/login.html">Login<' in page:
            return {"validuntil": -1, "trafficleft":-1, "premium": False}

      	if not '?op=logout">Logout<' in page:
            return {"validuntil": -1, "trafficleft": -1, "premium": False}
	
	#force directdowload setting
	#page = req.load("http://linestorage.com/?op=my_account",
	#	post={"usr_direct_downloads" : "1"}	

	return {"validultil": -1, "trafficleft": -1, "premium": True}


    def login(self, user, data, req):
        page = req.load('http://linestorage.com/login.html', 
		post={ "op" :  "login", "redirect" : "http://linestorage.com/", "login" : user, "password" : data["password"]
		, "submit" :"Submit"}, cookies = True)

        if 'Incorrect Login or Password' in page:
            self.wrongPassword()
