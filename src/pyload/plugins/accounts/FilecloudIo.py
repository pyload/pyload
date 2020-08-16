# -*- coding: utf-8 -*-

import json

from ..base.account import BaseAccount
from ..helpers import set_cookie


class FilecloudIo(BaseAccount):
    __name__ = "FilecloudIo"
    __type__ = "account"
    __version__ = "0.13"
    __status__ = "testing"

    __description__ = """FilecloudIo account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
    ]

    def grab_info(self, user, password, data):
        #: It looks like the first API request always fails, so we retry 5 times, it should work on the second try
        for _ in range(5):
            rep = self.load(
                "https://secure.filecloud.io/api-fetch_apikey.api",
                post={"username": user, "password": password},
            )
            rep = json.loads(rep)
            if rep["status"] == "ok":
                break
            elif (
                rep["status"] == "error"
                and rep["message"] == "no such user or wrong password"
            ):
                self.log_error(self._("Wrong username or password"))
                return {"valid": False, "premium": False}
        else:
            return {"premium": False}

        akey = rep["akey"]
        self.accounts[user]["akey"] = akey  #: Saved for hoster plugin
        rep = self.load(
            "http://api.filecloud.io/api-fetch_account_details.api", post={"akey": akey}
        )
        rep = json.loads(rep)

        if rep["is_premium"] == 1:
            return {"validuntil": float(rep["premium_until"]), "trafficleft": -1}
        else:
            return {"premium": False}

    def signin(self, user, password, data):
        set_cookie(self.req.cj, "secure.filecloud.io", "lang", "en")
        html = self.load("https://secure.filecloud.io/user-login.html")

        if not hasattr(self, "form_data"):
            self.form_data = {}

        self.form_data["username"] = user
        self.form_password = password

        html = self.load(
            "https://secure.filecloud.io/user-login_p.html", post=self.form_data
        )

        if "you have successfully logged in" not in html:
            self.fail_login()
