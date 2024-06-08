# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class FileStoreTo(BaseAccount):
    __name__ = "FileStoreTo"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = """Filestore.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_URL = "https://filestore.to/login"
    VALID_UNTIL_PATTERN = r'<small>Premium-Status</small><div class="value text-success">([\d\.]+? - [\d:]+)'

    def grab_info(self, user, password, data):
        premium = False
        validuntil = None

        html = self.load("https://filestore.to/konto")
        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y - %H:%M"))
            premium = validuntil > time.time()

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        html = self.load(self.LOGIN_URL)
        if 'href="logout"' in html:
            self.skip_login()

        else:
            html = self.load(
                self.LOGIN_URL,
                post={"Email": user, "Password": password, "Aktion": "Login"},
            )
            if 'href="logout"' not in html:
                self.fail_login()
