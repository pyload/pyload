# -*- coding: utf-8 -*-

import re

from ..base.account import BaseAccount


class DatoidCz(BaseAccount):
    __name__ = "DatoidCz"
    __type__ = "account"
    __version__ = "0.39"
    __status__ = "testing"

    __description__ = """Datoid.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", None)]

    def grab_info(self, user, password, data):
        html = self.load("https://datoid.cz/")

        m = re.search(r'"menu-bar-storage"></i> ([\d.,]+) ([\w^_]+)', html)
        trafficleft = self.parse_traffic(m.group(1), m.group(2)) if m else 0

        info = {"validuntil": -1, "trafficleft": trafficleft, "premium": True}

        return info

    def signin(self, user, password, data):
        html = self.load("https://datoid.cz/")
        if 'href="/muj-ucet">' in html:
            self.skip_login()

        html = self.load(
            "https://datoid.cz/prihlaseni?do=signInForm-submit",
            post={"username": user, "password": password},
        )

        if 'href="/muj-ucet">' not in html:
            self.fail_login()
