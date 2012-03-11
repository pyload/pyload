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

    @author: pking
"""

from module.plugins.Account import Account

class BitshareCom(Account):
    __name__ = "BitshareCom"
    __version__ = "0.11"
    __type__ = "account"
    __description__ = """Bitshare account plugin"""
    __author_name__ = ("Paul King")

    def loadAccountInfo(self, user, req):
        page = req.load("http://bitshare.com/mysettings.html")
    
        if "\"http://bitshare.com/myupgrade.html\">Free" in page:
            return {"validuntil": -1, "trafficleft":-1, "premium": False}

        if not '<input type="checkbox" name="directdownload" checked="checked" />' in page:
            self.core.log.warning(_("Activate direct Download in your Bitshare Account"))

        return {"validuntil": -1, "trafficleft": -1, "premium": True}


    def login(self, user, data, req):
        page = req.load("http://bitshare.com/login.html", post={ "user" : user, "password" : data["password"], "submit" :"Login"}, cookies=True)
        if "login" in req.lastEffectiveURL:
            self.wrongPassword()
