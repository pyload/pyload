# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class UptoboxCom(BaseAccount):
    __name__ = "UptoboxCom"
    __type__ = "account"
    __version__ = "0.29"
    __status__ = "testing"

    __description__ = """Uptobox.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("benbox69", "dev@tollet.me"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    LOGIN_URL = "https://uptobox.link/login"
    LOGIN_SKIP_PATTERN = r"https://uptobox\.link/logout"

    PREMIUM_PATTERN = r"Premium member"

    VALID_UNTIL_PATTERN = r'data-tippy-content="Expires on ([\d\-: ]+)"'

    def grab_info(self, user, password, data):
        html = self.load("https://uptobox.link/my_account")

        premium = re.search(self.PREMIUM_PATTERN, html) is not None

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            validuntil = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))

        else:
            self.log_error(self._("VALID_UNTIL_PATTERN not found"))
            validuntil = None

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        html = self.load(self.LOGIN_URL)

        if re.search(self.LOGIN_SKIP_PATTERN, html) is not None:
            self.skip_login()

        html = self.load(
            self.LOGIN_URL,
            post={"login": user, "password": password},
            ref=self.LOGIN_URL,
        )

        if re.search(self.LOGIN_SKIP_PATTERN, html) is None:
            self.fail_login()
