# -*- coding: utf-8 -*-

from ..base.account import BaseAccount


class BigfileTo(BaseAccount):
    __name__ = "BigfileTo"
    __type__ = "account"
    __version__ = "0.11"
    __status__ = "testing"

    __description__ = """bigfile.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Sasch", "gsasch@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def grab_info(self, user, password, data):
        html = self.load("https://www.bigfile.to/login.php")

        premium = '<a href="/logout.php"' in html
        trafficleft = -1 if premium else None

        return {
            "validuntil": None,
            "trafficleft": trafficleft,
            "premium": premium,
        }  # TODO: validuntil

    def signin(self, user, password, data):
        html = self.load(
            "https://www.bigfile.to/login.php",
            post={
                "userName": user,
                "userPassword": password,
                "autoLogin": "1",
                "action__login": "normalLogin",
            },
        )

        if "Login failed" in html:
            self.fail_login()
