# -*- coding: utf-8 -*-
import re
import time

from ..base.account import BaseAccount
from ..helpers import parse_html_form


class FshareVn(BaseAccount):
    __name__ = "FshareVn"
    __type__ = "account"
    __version__ = "0.22"
    __status__ = "testing"

    __description__ = """Fshare.vn account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    VALID_UNTIL_PATTERN = r">Hạn dùng:.+?>([\d/]+)</span>"
    LIFETIME_PATTERN = r"<dt>Lần đăng nhập trước:</dt>\s*<dd>.+?</dd>"
    TRAFFIC_LEFT_PATTERN = (
        r">Đã SD: </a>\s*([\d.,]+)(?:([\w^_]+))\s*/\s*([\d.,]+)(?:([\w^_]+))"
    )

    def grab_info(self, user, password, data):
        html = self.load("https://www.fshare.vn")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            trafficleft = (
                (
                    self.parse_traffic(m.group(3), m.group(4))
                    - self.parse_traffic(m.group(1), m.group(2))
                )
                if m
                else None
            )

        else:
            self.log_error(self._("TRAFFIC_LEFT_PATTERN not found"))

        if re.search(self.LIFETIME_PATTERN, html):
            self.log_debug("Lifetime membership detected")
            return {"validuntil": -1, "trafficleft": trafficleft, "premium": True}

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            premium = True
            validuntil = time.mktime(
                time.strptime(m.group(1) + " 23:59:59", "%d/%m/%Y %H:%M:%S")
            )

        else:
            premium = False
            validuntil = None
            trafficleft = None

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        html = self.load("https://www.fshare.vn/site/login")
        if 'href="/site/logout"' in html:
            self.skip_login()

        url, inputs = parse_html_form('id="form-signup"', html)
        if inputs is None:
            self.fail_login("Login form not found")

        inputs.update(
            {
                "LoginForm[email]": user,
                "LoginForm[password]": password,
                "LoginForm[rememberMe]": 1,
            }
        )

        html = self.load("https://www.fshare.vn/site/login", post=inputs)
        if 'href="/site/logout"' not in html:
            self.fail_login()
