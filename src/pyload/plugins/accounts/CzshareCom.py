# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class CzshareCom(BaseAccount):
    __name__ = "CzshareCom"
    __type__ = "account"
    __version__ = "0.28"
    __status__ = "testing"

    __description__ = """Czshare.com account plugin, now Sdilej.cz"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("ondrej", "git@ondrej.it"),
    ]

    CREDIT_LEFT_PATTERN = r'^\s+<div class="credit">\s+\n.+<strong>([\d,]+)(KB|MB|GB)</strong>\s+\n.+<!-- \.credit -->\s+$'
    VALID_UNTIL_PATTERN = r'^\s+<tr class="active">\s+\n.+\n\s+<td>([\d\.: ]+)</td>\s+$'

    def grab_info(self, user, password, data):
        premium = False
        validuntil = None
        trafficleft = None

        html = self.load("https://sdilej.cz/prehled_kreditu/")

        try:
            m = re.search(self.CREDIT_LEFT_PATTERN, html, re.MULTILINE)
            trafficleft = self.parse_traffic(m.group(1), m.group(2))

            v = re.search(self.VALID_UNTIL_PATTERN, html, re.MULTILINE)
            validuntil = time.mktime(time.strptime(v.group(1), "%d.%m.%y %H:%M"))

        except Exception as exc:
            self.log_error(exc)

        else:
            premium = True

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        html = self.load(
            "https://sdilej.cz/index.php",
            post={
                "Prihlasit": "Prihlasit",
                "login-password": password,
                "login-name": user,
            },
        )

        if '<div class="login' in html:
            self.fail_login()
