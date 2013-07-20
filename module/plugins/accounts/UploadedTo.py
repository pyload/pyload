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

from module.plugins.Account import Account
import re
from time import time

class UploadedTo(Account):
    __name__ = "UploadedTo"
    __version__ = "0.26"
    __type__ = "account"
    __description__ = """ul.net account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def loadAccountInfo(self, user, req):

        req.load("http://uploaded.net/language/en")
        html = req.load("http://uploaded.net/me")

        premium = '<a href="register"><em>Premium</em>' in html or '<em>Premium</em></th>' in html

        if premium:
            raw_traffic = re.search(r'<th colspan="2"><b class="cB">([^<]+)', html).group(1).replace('.', '')
            raw_valid = re.search(r"<td>Duration:</td>\s*<th>([^<]+)", html, re.MULTILINE).group(1).strip()

            traffic = int(self.parseTraffic(raw_traffic))

            if raw_valid == "unlimited":
                validuntil = -1
            else:
                raw_valid = re.findall(r"(\d+) (Week|weeks|days|day|hours|hour)", raw_valid)
                validuntil = time()
                for n, u in raw_valid:
                    validuntil += 3600 * int(n) * {"Week": 168, "weeks": 168, "days": 24, "day": 24, "hours": 1, "hour": 1}[u]

            return {"validuntil":validuntil, "trafficleft":traffic, "maxtraffic":50*1024*1024}
        else:
            return {"premium" : False, "validuntil" : -1}

    def login(self, user, data, req):

        req.load("http://uploaded.net/language/en")
        req.cj.setCookie("uploaded.net", "lang", "en")
        
        page = req.load("http://uploaded.net/io/login", post={ "id" : user, "pw" : data["password"], "_" : ""})

        if "User and password do not match!" in page:
            self.wrongPassword()
