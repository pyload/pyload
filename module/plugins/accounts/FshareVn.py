# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class FshareVn(Account):
    __name__    = "FshareVn"
    __type__    = "account"
    __version__ = "0.11"
    __status__  = "testing"

    __description__ = """Fshare.vn account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    VALID_UNTIL_PATTERN = ur'<dt>Thời hạn dùng:</dt>\s*<dd>([^<]+)</dd>'
    LIFETIME_PATTERN = ur'<dt>Lần đăng nhập trước:</dt>\s*<dd>.+?</dd>'
    TRAFFIC_LEFT_PATTERN = ur'<dt>Tổng Dung Lượng Tài Khoản</dt>\s*<dd.*?>([\d.]+) ([kKMG])B</dd>'
    DIRECT_DOWNLOAD_PATTERN = ur'<input type="checkbox"\s*([^=>]*)[^>]*/>Kích hoạt download trực tiếp</dt>'


    def parse_info(self, user, password, data, req):
        html = self.load("http://www.fshare.vn/account_info.php")

        if re.search(self.LIFETIME_PATTERN, html):
            self.log_debug("Lifetime membership detected")
            trafficleft = self.get_traffic_left()
            return {'validuntil': -1, 'trafficleft': trafficleft, 'premium': True}

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), '%I:%M:%S %p %d-%m-%Y'))
            trafficleft = self.get_traffic_left()
        else:
            premium = False
            validuntil = None
            trafficleft = None

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, password, data, req):
        html = self.load("https://www.fshare.vn/login.php",
                         post={'LoginForm[email]'     : user,
                               'LoginForm[password]'  : password,
                               'LoginForm[rememberMe]': 1,
                               'yt0'                  : "Login"})

        if not re.search(r'<img\s+alt="VIP"', html):
            self.login_fail()


    def get_traffic_left(self):
        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        return self.parse_traffic(m.group(1) + m.group(2)) if m else 0
