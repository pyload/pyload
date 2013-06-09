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

    @author: RaNaN
"""

from module.plugins.Account import Account
import re
from time import time

class FilesMailRu(Account):
    __name__ = "FilesMailRu"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """filesmail.ru account plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def loadAccountInfo(self, user, req):
        return {"validuntil": None, "trafficleft": None}
    
    def login(self, user, data,req):
        user, domain = user.split("@")

        page = req.load("http://swa.mail.ru/cgi-bin/auth", None, { "Domain" : domain, "Login": user, "Password" : data['password'], "Page" : "http://files.mail.ru/"}, cookies=True)

        if "Неверное имя пользователя или пароль" in page: # @TODO seems not to work
            self.wrongPassword()
