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

class HellshareCz(Account):
    __name__ = "HellshareCz"
    __version__ = "0.11"
    __type__ = "account"
    __description__ = """hellshare.cz account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    CREDIT_LEFT_PATTERN = r'<div class="credit-link">\s*<table>\s*<tr>\s*<th>(\d+)</th>'

    def loadAccountInfo(self, user, req):
        self.relogin(user)
        html = req.load("http://www.hellshare.com/")

        found = re.search(self.CREDIT_LEFT_PATTERN, html)
        if found is None:
            credits = 0
        else:
            credits = int(found.group(1)) * 1024

        return {"validuntil": -1, "trafficleft": credits}

    def login(self, user, data, req):

        html = req.load('http://www.hellshare.com/login?do=loginForm-submit', post={
                "login": "Log in",
                "password": data["password"],
                "username": user
                })

        if "<p>You input a wrong user name or wrong password</p>" in html:
            self.wrongPassword()