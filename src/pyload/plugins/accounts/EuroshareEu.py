# -*- coding: utf-8 -*-

import json
import re
import time

from ..base.account import BaseAccount


class EuroshareEu(BaseAccount):
    __name__ = "EuroshareEu"
    __type__ = "account"
    __version__ = "0.12"
    __status__ = "testing"

    __description__ = """Euroshare.eu account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def grab_info(self, user, password, data):
        html = self.load("http://euroshare.eu/", get={"lang": "en"})

        m = re.search(
            r'<span class="btn btn--nav green darken-3">Premium account until: (\d+/\d+/\d+ \d+:\d+:\d+)<',
            html,
        )
        if m is None:
            premium = False
            validuntil = -1
        else:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d/%m/%Y %H:%M:%S"))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        html = self.load("http://euroshare.eu/login.html")

        if r'href="http://euroshare.eu/logout.html"' in html:
            self.skip_login()

        json_data = json.loads(
            self.load(
                "http://euroshare.eu/ajax/_account_login.ajax.php",
                post={
                    "username": user,
                    "password": password,
                    "remember": "false",
                    "backlink": "",
                },
            )
        )

        if json_data.get("login_status") != "success":
            self.fail_login()
