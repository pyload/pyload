# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class UpstoreNet(BaseAccount):
    __name__ = "UpstoreNet"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Upstore.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")
    ]

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = True

        html = self.load("https://upstore.net/stat/download",
                         get={'lang': "en"})

        m = re.search(r"Downloaded in last 24 hours: ([\d.,]+) of ([\d.,]+) GB", html)
        if m is not None:
            trafficleft = self.parse_traffic(m.group(2), "GB") - self.parse_traffic(m.group(1), "GB")

        if "eternal premium" in html:
            validuntil = -1

        else:
            m = re.search(r'premium till\s*(\d{1,2}/\d{1,2}/\d{2})', html)
            if m is not None:
                validuntil = time.mktime(time.strptime(m.group(1) + " 23:59:59", '%m/%d/%y %H:%M:%S'))

            else:
                m = re.search(r'premium till\s*([a-zA-Z.]+\s*\d{1,2}\s*,\s*(\d{4}|\d{2}))', html)
                if m is not None:
                    validuntil = time.mktime(time.strptime(m.group(1) + " 23:59:59", '%B %d , %y %H:%M:%S'))

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        login_url = "https://upstore.net/account/login"
        html = self.load(login_url)
        if "/account/logout" in html:
            self.skip_login()

        html = self.load(login_url,
                         post={'url': "https://upstore.net",
                               'email': user,
                               'password': password,
                               'send': "Login"})

        if "/account/logout" not in html:
            self.fail_login()
