# -*- coding: utf-8 -*-
import re
import time

from ..base.account import BaseAccount
from ..helpers import parse_html_form, set_cookie


class TurbobitNet(BaseAccount):
    __name__ = "TurbobitNet"
    __type__ = "account"
    __version__ = "0.12"
    __status__ = "testing"

    __description__ = """TurbobitNet account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    LOGIN_FAIL_PATTERN = r">(?:E-Mail address appears to be invalid\. Please try again|Incorrect login or password)</div>"

    def grab_info(self, user, password, data):
        html = self.load("https://turbobit.net/")

        m = re.search(r">Turbo access till ([\d.]+)<", html)
        if m is not None:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y"))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def signin(self, user, password, data):
        set_cookie(self.req.cj, "turbobit.net", "user_lang", "en")

        self.data = self.load("https://turbobit.net/login")

        if "<a href='/user/logout'" in self.data:
            self.skip_login()

        action, inputs = parse_html_form(
            'class="form-horizontal login mail"', self.data
        )
        if not inputs:
            self.fail_login(self._("Login form not found"))

        inputs["user[login]"] = user
        inputs["user[pass]"] = password
        inputs["user[submit]"] = "Sign in"

        if inputs.get("user[captcha_type]"):
            self.fail_login(
                self._(
                    "Logging in with captcha is not supported, please disable catcha in turbobit's account settings"
                )
            )

        self.data = self.load("https://turbobit.net/user/login", post=inputs)

        if "<a href='/user/logout'" in self.data:
            self.log_debug("Login successful")

        elif re.search(self.LOGIN_FAIL_PATTERN, self.data):
            self.fail_login()

        elif ">Please enter the captcha code.</div>" in self.data:
            self.fail_login(
                self._(
                    "Logging in with captcha is not supported, please disable catcha in turbobit's account settings"
                )
            )

        else:
            self.fail_login(self._("Unknown response"))
