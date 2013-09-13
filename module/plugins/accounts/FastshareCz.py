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

import re
from module.plugins.Account import Account
from module.utils import parseFileSize


class FastshareCz(Account):
    __name__ = "FastshareCz"
    __version__ = "0.03"
    __type__ = "account"
    __description__ = """fastshare.cz account plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    CREDIT_PATTERN = r'(?:Kredit|Credit)\s*</td>\s*<td[^>]*>([\d. \w]+)&nbsp;'

    def loadAccountInfo(self, user, req):
        html = req.load("http://www.fastshare.cz/user", decode=True)

        found = re.search(self.CREDIT_PATTERN, html)
        if found:
            trafficleft = parseFileSize(found.group(1)) / 1024
            premium = True if trafficleft else False
        else:
            trafficleft = None
            premium = False

        return {"validuntil": -1, "trafficleft": trafficleft, "premium": premium}

    def login(self, user, data, req):
        req.load('http://www.fastshare.cz/login')  # Do not remove or it will not login
        html = req.load('http://www.fastshare.cz/sql.php', post={
            "heslo": data['password'],
            "login": user
        }, decode=True)

        if u'>Špatné uživatelské jméno nebo heslo.<' in html:
            self.wrongPassword()