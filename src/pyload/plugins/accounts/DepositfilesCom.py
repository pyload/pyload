# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class DepositfilesCom(BaseAccount):
    __name__ = "DepositfilesCom"
    __type__ = "account"
    __version__ = "0.39"
    __status__ = "testing"

    __description__ = """Depositfiles.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("mkaay", "mkaay@mkaay.de"),
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    def grab_info(self, user, password, data):
        html = self.load("https://dfiles.eu/de/gold/")
        validuntil = re.search(
            r"Sie haben Gold Zugang bis: <b>(.*?)</b></div>", html
        ).group(1)

        validuntil = time.mktime(time.strptime(validuntil, "%Y-%m-%d %H:%M:%S"))

        return {"validuntil": validuntil, "trafficleft": -1}

    def signin(self, user, password, data):
        html = self.load(
            "https://dfiles.eu/de/login.php",
            get={"return": "/de/gold/payment.php"},
            post={"login": user, "password": password},
        )

        if (
            r'<div class="error_message">Sie haben eine falsche Benutzername-Passwort-Kombination verwendet.</div>'
            in html
        ):
            self.fail_login()
