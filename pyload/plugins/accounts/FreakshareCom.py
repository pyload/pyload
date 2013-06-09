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
from time import strptime, mktime

from module.plugins.Account import Account

class FreakshareCom(Account):
    __name__ = "FreakshareCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """freakshare.com account plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def loadAccountInfo(self, user, req):
        page = req.load("http://freakshare.com/")

        validuntil = r"ltig bis:</td>\s*<td><b>([0-9 \-:.]+)</b></td>"
        validuntil = re.search(validuntil, page, re.MULTILINE)
        validuntil = validuntil.group(1).strip()
        validuntil = mktime(strptime(validuntil, "%d.%m.%Y - %H:%M"))

        traffic = r"Traffic verbleibend:</td>\s*<td>([^<]+)"
        traffic = re.search(traffic, page, re.MULTILINE)
        traffic = traffic.group(1).strip()
        traffic = self.parseTraffic(traffic)

        return {"validuntil": validuntil, "trafficleft": traffic}

    def login(self, user, data, req):
        page = req.load("http://freakshare.com/login.html", None, { "submit" : "Login", "user" : user, "pass" : data['password']}, cookies=True)

        if "Falsche Logindaten!" in page or "Wrong Username or Password!" in page:
            self.wrongPassword()
