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
    
    @author: DHMH
"""

from module.plugins.Account import Account
import re
from time import strptime, mktime
from module.utils import formatSize, parseFileSize

class OronCom(Account):
    __name__ = "OronCom"
    __version__ = "0.13"
    __type__ = "account"
    __description__ = """oron.com account plugin"""
    __author_name__ = ("DHMH")
    __author_mail__ = ("DHMH@pyload.org")

    def loadAccountInfo(self, req):
        req.load("http://oron.com/?op=change_lang&lang=german")
        src = req.load("http://oron.com/?op=my_account").replace("\n", "")
        validuntil = re.search(r"<td>Premiumaccount läuft bis:</td>\s*<td>(.*?)</td>", src)
        if validuntil:
            validuntil = validuntil.group(1)
            validuntil = int(mktime(strptime(validuntil, "%d %B %Y")))
            trafficleft = re.search(r'<td>Download Traffic verfügbar:</td>\s*<td>(.*?)</td>', src).group(1)
            self.logDebug("Oron left: " + formatSize(parseFileSize(trafficleft)))
            trafficleft = int(self.parseTraffic(trafficleft))
            premium = True
        else:
            validuntil = -1
            trafficleft = None
            premium = False
        tmp = {"validuntil": validuntil, "trafficleft": trafficleft, "premium" : premium}
        return tmp

    def login(self, req):
        req.load("http://oron.com/?op=change_lang&lang=german")
        page = req.load("http://oron.com/login", post={"login": self.loginname, "password": self.password, "op": "login"})
        if r'<b class="err">Login oder Passwort falsch</b>' in page:
            self.wrongPassword()

