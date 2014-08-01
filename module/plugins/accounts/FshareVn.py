# -*- coding: utf-8 -*-

from time import mktime, strptime
from pycurl import REFERER
import re

from module.plugins.Account import Account


class FshareVn(Account):
    __name__ = "FshareVn"
    __type__ = "account"
    __version__ = "0.07"

    __description__ = """Fshare.vn account plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    VALID_UNTIL_PATTERN = ur'<dt>Thời hạn dùng:</dt>\s*<dd>([^<]+)</dd>'
    LIFETIME_PATTERN = ur'<dt>Lần đăng nhập trước:</dt>\s*<dd>[^<]+</dd>'
    TRAFFIC_LEFT_PATTERN = ur'<dt>Tổng Dung Lượng Tài Khoản</dt>\s*<dd[^>]*>([0-9.]+) ([kKMG])B</dd>'
    DIRECT_DOWNLOAD_PATTERN = ur'<input type="checkbox"\s*([^=>]*)[^>]*/>Kích hoạt download trực tiếp</dt>'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.fshare.vn/account_info.php", decode=True)

        if re.search(self.LIFETIME_PATTERN, html):
            self.logDebug("Lifetime membership detected")
            trafficleft = self.getTrafficLeft()
            return {"validuntil": -1, "trafficleft": trafficleft, "premium": True}

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            premium = True
            validuntil = mktime(strptime(m.group(1), '%I:%M:%S %p %d-%m-%Y'))
            trafficleft = self.getTrafficLeft()
        else:
            premium = False
            validuntil = None
            trafficleft = None

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}

    def login(self, user, data, req):
        req.http.c.setopt(REFERER, "https://www.fshare.vn/login.php")

        html = req.load('https://www.fshare.vn/login.php', post={
            "login_password": data['password'],
            "login_useremail": user,
            "url_refe": "http://www.fshare.vn/index.php"
        }, referer=True, decode=True)

        if not re.search(r'<img\s+alt="VIP"', html):
            self.wrongPassword()

    def getTrafficLeft(self):
        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        return float(m.group(1)) * 1024 ** {'k': 0, 'K': 0, 'M': 1, 'G': 2}[m.group(2)] if m else 0
