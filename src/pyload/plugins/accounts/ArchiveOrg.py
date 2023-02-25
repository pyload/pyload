# -*- coding: utf-8 -*-

import json

from pyload.core.network.http.exceptions import BadHeader

from ..base.account import BaseAccount


class ArchiveOrg(BaseAccount):
    __name__ = "ArchiveOrg"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Archive.org account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_URL = "https://archive.org/account/login"
    LOGIN_CHECK_URL = "https://archive.org/account/index.php"

    def grab_info(self, user, password, data):
        return {'validuntil': None,
                'trafficleft': None,
                'premium': False}

    def signin(self, user, password, data):
        html = self.load(self.LOGIN_CHECK_URL)
        if "<title>cannot find account</title>" not in html:
            self.skip_login()

        else:
            self.load(self.LOGIN_URL)
            try:
                html = self.load(self.LOGIN_URL, post={
                    "username": user,
                    "password": password,
                    "remember": "true",
                    "referer": "https://archive.org/",
                    "login": "true",
                    "submit_by_js": "true"
                })
            except BadHeader as exc:
                self.fail_login(str(exc))

            else:
                json_data = json.loads(html)
                if json_data["status"] != "ok":
                    self.fail_login()
