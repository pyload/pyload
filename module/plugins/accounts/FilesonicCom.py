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

import re
from time import mktime, strptime

from module.plugins.Account import Account

class FilesonicCom(Account):
    __name__ = "FilesonicCom"
    __version__ = "0.2"
    __type__ = "account"
    __description__ = """filesonic.com account plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def loadAccountInfo(self, user, req):
        src = req.load("http://www.filesonic.com/user/settings").decode("utf8")

        validuntil = re.search(r'\d+-\d+-\d+ \d+:\d+:\d+', src).group(0)
        validuntil = int(mktime(strptime(validuntil, "%Y-%m-%d %H:%M:%S")))
        tmp = {"validuntil": validuntil, "trafficleft": -1}
        return tmp

    def login(self, user, data, req):
        post_vars = {
            "email": user,
            "password": data["password"],
            "rememberMe" : 1
        }
        page = req.load("http://www.filesonic.com/user/login", cookies=True, post=post_vars).decode("utf8")

        if "Provided password does not match." in page or "You must be logged in to view this page." in page:
            self.wrongPassword()
