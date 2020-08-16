# -*- coding: utf-8 -*-

import re

from ..base.account import BaseAccount
from ..helpers import set_cookie


class FastshareCz(BaseAccount):
    __name__ = "FastshareCz"
    __type__ = "account"
    __version__ = "0.17"
    __status__ = "testing"

    __description__ = """Fastshare.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("ondrej", "git@ondrej.it"),
    ]

    CREDIT_PATTERN = r'<a href="/user">.+<span>\(([\d\.]+) ([MGT]+B)\)</span></a>'

    def grab_info(self, user, password, data):
        validuntil = -1
        trafficleft = None
        premium = False

        html = self.load("https://www.fastshare.cz/user")

        m = re.search(self.CREDIT_PATTERN, html)
        if m is not None:
            trafficleft = self.parse_traffic(m.group(1), m.group(2))

        premium = bool(trafficleft)

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        set_cookie(self.req.cj, "fastshare.cz", "lang", "en")

        # NOTE: Do not remove or it will not login
        self.load("https://www.fastshare.cz/login")

        html = self.load(
            "https://www.fastshare.cz/sql.php", post={"login": user, "heslo": password}
        )

        if ">Wrong username or password" in html:
            self.fail_login()
