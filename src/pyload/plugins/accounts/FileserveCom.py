# -*- coding: utf-8 -*-

import json
import time

from ..base.account import BaseAccount


class FileserveCom(BaseAccount):
    __name__ = "FileserveCom"
    __type__ = "account"
    __version__ = "0.27"
    __status__ = "testing"

    __description__ = """Fileserve.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de")]

    def grab_info(self, user, password, data):
        html = self.load(
            "http://app.fileserve.com/api/login/",
            post={"username": user, "password": password, "submit": "Submit+Query"},
        )
        res = json.loads(html)

        if res["type"] == "premium":
            validuntil = time.mktime(
                time.strptime(res["expireTime"], "%Y-%m-%d %H:%M:%S")
            )
            return {"trafficleft": res["traffic"], "validuntil": validuntil}
        else:
            return {"premium": False, "trafficleft": None, "validuntil": None}

    def signin(self, user, password, data):
        html = self.load(
            "http://app.fileserve.com/api/login/",
            post={"username": user, "password": password, "submit": "Submit+Query"},
        )
        res = json.loads(html)

        if not res["type"]:
            self.fail_login()

        #: Login at fileserv html
        self.load(
            "http://www.fileserve.com/login.php",
            post={
                "loginUserName": user,
                "loginUserPassword": password,
                "autoLogin": "checked",
                "loginFormSubmit": "Login",
            },
        )
