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
"""

import re

from module.plugins.Account import Account
from module.utils import parseFileSize


class StahnuTo(Account):
    __name__ = "StahnuTo"
    __version__ = "0.02"
    __type__ = "account"

    __description__ = """StahnuTo account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.stahnu.to/")

        m = re.search(r'>VIP: (\d+.*)<', html)
        trafficleft = parseFileSize(m.group(1)) * 1024 if m else 0

        return {"premium": trafficleft > (512 * 1024), "trafficleft": trafficleft, "validuntil": -1}

    def login(self, user, data, req):
        html = req.load("http://www.stahnu.to/login.php", post={
            "username": user,
            "password": data['password'],
            "submit": "Login"})

        if not '<a href="logout.php">' in html:
            self.wrongPassword()
