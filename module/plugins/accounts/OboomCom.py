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

    @author: stanley
"""

import urllib
import json
import time

from module.plugins.Account import Account
from module.lib.beaker.crypto.pbkdf2 import PBKDF2


class OboomCom(Account):
    __name__ = "OboomCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """Oboom.com account plugin"""
    __author_name__ = "stanley"
    __author_mail__ = "stanley.foerster@gmail.com"

    def loadAccountData(self, user, req):
        passwd = self.accounts[user]["password"]
        salt = passwd[::-1]
        pbkdf2 = PBKDF2(passwd, salt, 1000).hexread(16)
        params = urllib.urlencode({"auth": user, "pass": pbkdf2})
        result = json.loads(req.load("https://www.oboom.com/1.0/login?%s" % params))
        if not result[0] == 200:
            self.logWarning("Failed to log in: %s" % result[1])
            self.wrongPassword()
        return result[1]

    def loadAccountInfo(self, name, req):
        accountData = self.loadAccountData(name, req)
        userData = accountData["user"]

        if "premium_unix" in userData:
            validUntilUtc = int(userData["premium_unix"])
            if validUntilUtc > int(time.time()):
                premium = True
                validUntil = validUntilUtc
                traffic = userData["traffic"]
                trafficLeft = traffic["current"]
                maxTraffic = traffic["max"]
                session = accountData["session"]
                return {"premium": premium,
                        "validuntil": validUntil,
                        "trafficleft": trafficLeft/1024,
                        "maxtraffic": maxTraffic/1024,
                        "session": session
                        }
        return {"premium": False, "validuntil": -1}

    def login(self, user, data, req):
        self.loadAccountData(user, req)