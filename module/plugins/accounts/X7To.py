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

    @author: ernieb
"""

import re
from time import strptime, mktime

from module.plugins.Account import Account

class X7To(Account):
    __name__ = "X7To"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """X7.To account plugin"""
    __author_name__ = ("ernieb")
    __author_mail__ = ("ernieb")

    def loadAccountInfo(self, user, req):
        page = req.load("http://www.x7.to/my")

        validCheck = re.search("Premium-Mitglied bis ([0-9]*-[0-9]*-[0-9]*)", page, re.IGNORECASE)
        if validCheck:
            valid = validCheck.group(1)
            valid = int(mktime(strptime(valid, "%Y-%m-%d")))
        else:
            validCheck = re.search("Premium member until ([0-9]*-[0-9]*-[0-9]*)", page, re.IGNORECASE)
            if validCheck:
                valid = validCheck.group(1)
                valid = int(mktime(strptime(valid, "%Y-%m-%d")))
            else:
                valid = 0

        trafficleft = re.search(r'<em style="white-space:nowrap">([\d]*[,]?[\d]?[\d]?) (KB|MB|GB)</em>', page, re.IGNORECASE)
        if trafficleft:
            units = float(trafficleft.group(1).replace(",", "."))
            pow = {'KB': 0, 'MB': 1, 'GB': 2}[trafficleft.group(2)]
            trafficleft = int(units * 1024 ** pow)
        else:
            trafficleft = -1

        return {"trafficleft": trafficleft, "validuntil": valid}


    def login(self, user, data, req):
        #req.cj.setCookie("share.cx", "lang", "english")
        page = req.load("http://x7.to/lang/en", None, {})
        page = req.load("http://x7.to/james/login", None,
                {"redirect": "http://www.x7.to/", "id": user, "pw": data['password'], "submit": "submit"})

        if "Username and password are not matching." in page:
            self.wrongPassword()
