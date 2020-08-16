# -*- coding: utf-8 -*-

import re
import time
import urllib.parse

from ..base.account import BaseAccount


class FilejungleCom(BaseAccount):
    __name__ = "FilejungleCom"
    __type__ = "account"
    __version__ = "0.19"
    __status__ = "testing"

    __description__ = """Filejungle.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    login_timeout = 60

    URL = "http://filejungle.com/"
    TRAFFIC_LEFT_PATTERN = r'"/extend_premium\.php">Until (\d+ \w+ \d+)<br'
    LOGIN_FAILED_PATTERN = (
        r'<span htmlfor="loginUser(Name|Password)" generated="true" class="fail_info">'
    )

    def grab_info(self, user, password, data):
        html = self.load(self.URL + "dashboard.php")
        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d %b %Y"))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def signin(self, user, password, data):
        html = self.load(
            urllib.parse.urljoin(self.URL, "login.php"),
            post={
                "loginUserName": user,
                "loginUserPassword": password,
                "loginFormSubmit": "Login",
                "recaptcha_challenge_field": "",
                "recaptcha_response_field": "",
                "recaptcha_shortencode_field": "",
            },
        )

        if re.search(self.LOGIN_FAILED_PATTERN, html):
            self.fail_login()
