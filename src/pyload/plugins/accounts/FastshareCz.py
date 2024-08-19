# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount
from ..helpers import set_cookie


class FastshareCz(BaseAccount):
    __name__ = "FastshareCz"
    __type__ = "account"
    __version__ = "0.19"
    __status__ = "testing"

    __description__ = """Fastshare.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("ondrej", "git@ondrej.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    TRAFFICLEFT_PATTERN = r"<td>([\d\.]+) ([KMGT]B)\s*</td>"
    VALID_UNTILL_PATTERN = r">Active until ([\d.]+)<"

    def grab_info(self, user, password, data):
        html = self.load("https://fastshare.cz/user")

        m = re.search(self.VALID_UNTILL_PATTERN, html)
        if m is not None:
            validuntil = time.mktime(
                time.strptime(m.group(1) + " 23:59:59", "%d.%m.%Y %H:%M:%S")
            )
            premium = True
            trafficleft = -1

        else:
            validuntil = -1
            m = re.search(self.TRAFFICLEFT_PATTERN, html)
            if m is not None:
                trafficleft = self.parse_traffic(m.group(1), m.group(2))
                premium = bool(trafficleft)
                if not premium:
                    trafficleft = None

            elif ">Unlimited downloading<" in html:
                premium = True
                trafficleft = -1
                validuntil = None

            else:
                premium = False
                trafficleft = None

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        set_cookie(self.req.cj, "fastshare.cz", "lang", "en")

        html = self.load("https://fastshare.cz/user")
        if 'href="/logout.php"' in html:
            self.skip_login()

        html = self.load(
            "https://fastshare.cz/sql.php",
            post={"login": user, "heslo": password},
        )

        if 'href="/logout.php"' not in html:
            self.fail_login()
