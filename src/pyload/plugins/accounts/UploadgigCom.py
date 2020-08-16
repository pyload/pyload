# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class UploadgigCom(BaseAccount):
    __name__ = "UploadgigCom"
    __type__ = "account"
    __version__ = "0.03"
    __status__ = "testing"

    __description__ = """UploadgigCom account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_SKIP_PATTERN = r"You are currently logged in."

    PREMIUM_PATTERN = (
        r'<dt>Premium download:</dt>\s*<dd class="text-success">Active</dd>'
    )
    VALID_UNTIL_PATTERN = r"<dt>Package expire date:</dt>\s*<dd>([\d/]+)"
    TRAFFIC_LEFT_PATTERN = r"<dt>Daily traffic usage:</dt>\s*<dd>(?P<S1>[\d.,]+) (?:(?P<U1>[\w^_]+) )?/ (?P<S2>[\d.,]+) (?P<U2>[\w^_]+)"

    def grab_info(self, user, password, data):
        html = self.load("https://uploadgig.com/user/my_account")

        premium = re.search(self.PREMIUM_PATTERN, html) is not None

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is None:
            trafficleft = None

        else:
            trafficleft = self.parse_traffic(
                m.group("S2"), m.group("U2")
            ) - self.parse_traffic(m.group("S1"), m.group("U1") or m.group("U2"))

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is None:
            validuntil = None

        else:
            validuntil = time.mktime(time.strptime(m.group(1), "%Y/%m/%d"))

        return {
            "premium": premium,
            "trafficleft": trafficleft,
            "validuntil": validuntil,
        }

    def signin(self, user, password, data):
        html = self.load("https://uploadgig.com/login/form")

        if self.LOGIN_SKIP_PATTERN in html:
            self.skip_login()

        m = re.search(r'name="csrf_tester" value="(\w+?)"', html)
        if m is None:
            self.fail_login()

        html = self.load(
            "https://uploadgig.com/login/do_login",
            post={
                "email": user,
                "pass": password,
                "csrf_tester": m.group(1),
                "rememberme": 1,
            },
        )

        if '"state":"1"' not in html:
            self.fail_login()

    @property
    def logged(self):
        """
        Checks if user is still logged in.
        """
        if not self.user:
            return False

        self.sync()

        if (
            self.info["login"]["timestamp"] == 0
            or self.timeout != -1
            and self.info["login"]["timestamp"] + self.timeout < time.time()
            or self.req
            and not self.req.cj.parse_cookie("fs_secure")
        ):

            self.log_debug(f"Reached login timeout for user `{self.user}`")
            return False
        else:
            return True
