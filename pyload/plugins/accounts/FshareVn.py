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

from time import mktime, strptime
from pycurl import REFERER
import re

from module.plugins.Account import Account


class FshareVn(Account):
    __name__ = "FshareVn"
    __version__ = "0.06"
    __type__ = "account"
    __description__ = """fshare.vn account plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    VALID_UNTIL_PATTERN = ur'<dt>Thời hạn dùng:</dt>\s*<dd>([^<]+)</dd>'
    LIFETIME_PATTERN = ur'<dt>Lần đăng nhập trước:</dt>\s*<dd>[^<]+</dd>'
    TRAFFIC_LEFT_PATTERN = ur'<dt>Tổng Dung Lượng Tài Khoản</dt>\s*<dd[^>]*>([0-9.]+) ([kKMG])B</dd>'
    DIRECT_DOWNLOAD_PATTERN = ur'<input type="checkbox"\s*([^=>]*)[^>]*/>Kích hoạt download trực tiếp</dt>'

    def loadAccountInfo(self, user, req):
        self.html = req.load("http://www.fshare.vn/account_info.php", decode=True)

        if re.search(self.LIFETIME_PATTERN, self.html):
            self.logDebug("Lifetime membership detected")
            trafficleft = self.getTrafficLeft()
            return {"validuntil": -1, "trafficleft": trafficleft, "premium": True}

        found = re.search(self.VALID_UNTIL_PATTERN, self.html)
        if found:
            premium = True
            validuntil = mktime(strptime(found.group(1), '%I:%M:%S %p %d-%m-%Y'))
            trafficleft = self.getTrafficLeft()
        else:
            premium = False
            validuntil = None
            trafficleft = None

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}

    def login(self, user, data, req):
        req.http.c.setopt(REFERER, "https://www.fshare.vn/login.php")

        self.html = req.load('https://www.fshare.vn/login.php', post={
            "login_password": data['password'],
            "login_useremail": user,
            "url_refe": "https://www.fshare.vn/login.php"
        }, referer=True, decode=True)

        if not '<img alt="VIP"' in self.html:
            self.wrongPassword()

    def getTrafficLeft(self):
        found = re.search(self.TRAFFIC_LEFT_PATTERN, self.html)
        return float(found.group(1)) * 1024 ** {'k': 0, 'K': 0, 'M': 1, 'G': 2}[found.group(2)] if found else 0
