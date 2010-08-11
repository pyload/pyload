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
    
    @author: mkaay
"""

from module.plugins.Account import Account

class ShareonlineBiz(Account):
    __name__ = "ShareonlineBiz"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """share-online.biz account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    #@TODO: account info
    
    def login(self, user, data):
        req = self.core.requestFactory.getRequest(self.__name__, user)
        post_vars = {"user": user,
                        "pass": data["password"],
                        "l_rememberme":"1"}
        req.lastURL = "http://www.share-online.biz/alpha/"
        req.load("https://www.share-online.biz/alpha/user/login", cookies=True, post=post_vars)
