# -*- coding: utf-8 -*-

from ..base.account import BaseAccount
from ..helpers import set_cookie


class FourSharedCom(BaseAccount):
    __name__ = "FourSharedCom"
    __type__ = "account"
    __version__ = "0.13"
    __status__ = "testing"

    __description__ = """FourShared.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
    ]

    def grab_info(self, user, password, data):
        #: Free mode only for now
        return {"premium": False}

    def signin(self, user, password, data):
        set_cookie(self.req.cj, "4shared.com", "4langcookie", "en")

        res = self.load(
            "https://www.4shared.com/web/login",
            post={
                "login": user,
                "password": password,
                "remember": "on",
                "_remember": "on",
                "returnTo": "http://www.4shared.com/account/home.jsp",
            },
        )

        if "Please log in to access your 4shared account" in res:
            self.fail_login()
