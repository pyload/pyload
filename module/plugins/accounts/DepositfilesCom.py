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

import re
from time import strptime, mktime

from module.plugins.Account import Account


class DepositfilesCom(Account):
    __name__ = "DepositfilesCom"
    __version__ = "0.2"
    __type__ = "account"
    __description__ = """Depositfiles.com account plugin"""
    __author_name__ = ("mkaay", "stickell")
    __author_mail__ = ("mkaay@mkaay.de", "l.stickell@yahoo.it")

    def loadAccountInfo(self, user, req):
        src = req.load("http://depositfiles.com/de/gold/")
        validuntil = re.search(r"Sie haben Gold Zugang bis: <b>(.*?)</b></div>", src).group(1)

        validuntil = int(mktime(strptime(validuntil, "%Y-%m-%d %H:%M:%S")))

        return {"validuntil": validuntil, "trafficleft": -1}

    def login(self, user, data, req):
        req.load("http://depositfiles.com/de/gold/payment.php")
        src = req.load("http://depositfiles.com/de/login.php", get={"return": "/de/gold/payment.php"},
                       post={"login": user, "password": data["password"]})
        if r'<div class="error_message">Sie haben eine falsche Benutzername-Passwort-Kombination verwendet.</div>' in src:
            self.wrongPassword()
