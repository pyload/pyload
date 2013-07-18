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
from time import strptime, mktime

class DepositfilesCom(Account):
    __name__ = "DepositfilesCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """depositfiles.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def loadAccountInfo(self, user, req):

        src = req.load("http://dfiles.eu/en/gold/")
        validuntil = re.search("You have Gold access until: <b>(.*?)</b></div>", src).group(1)

        validuntil = int(mktime(strptime(validuntil, "%Y-%m-%d %H:%M:%S")))

        tmp = {"validuntil": validuntil, "trafficleft": -1}
        return tmp
    
    def login(self, user, data, req):

        req.load("http://dfiles.eu/en")
        version = req.load("http://dfiles.eu/en/api/get_downloader_version.php")
        agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.8.1.20) DepositFiles/FileManager %s' % version

        req.putHeader('User-Agent', agent)

        src = req.load("http://dfiles.eu/en/login.php", post={"login": user, "password": data["password"]})
        if "Current password is invalid" in src:
            self.wrongPassword()
