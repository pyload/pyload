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

class FilecloudIo(Account):
    __name__ = "FilecloudIo"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """FilecloudIo account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
        
    def loadAccountInfo(self, user, req):                           
        return ({"validuntil": -1, "trafficleft": -1, "premium": False})
    
    def login(self, user, data, req):
        req.cj.setCookie("secure.filecloud.io", "lang", "en")
        html = req.load('https://secure.filecloud.io/user-login.html')
        
        if not hasattr(self, "form_data"):
            self.form_data = {}
                       
        self.form_data["username"] = user
        self.form_data["password"] = data['password']
    
        html = req.load('https://secure.filecloud.io/user-login_p.html',
                    post = self.form_data,
                    multipart = True)
        
        self.logged_in = True if "you have successfully logged in - filecloud.io" in html else False
        self.form_data = {}
            