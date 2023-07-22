# -*- coding: utf-8 -*-

import json
import re
import time

from pyload.core.datatypes.pyfile import PyFile

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.account import BaseAccount
from ..helpers import parse_html_form


class UploadgigCom(BaseAccount):
    __name__ = "UploadgigCom"
    __type__ = "account"
    __version__ = "0.07"
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

        url, inputs = parse_html_form('id="login_form"', html)
        if inputs is None:
            self.fail_login("Login form not found")

        inputs["email"] = user
        inputs["pass"] = password

        if '<div class="row" id="parent_captcha_container">' in html:
            # dummy pyfile
            pyfile = PyFile(
                self.pyload.files,
                -1,
                "https://uploadgig.com",
                "https://uploadgig.com",
                0,
                0,
                "",
                self.classname,
                -1,
                -1,
            )
            pyfile.plugin = self
            recaptcha = ReCaptcha(pyfile)
            captcha_key = recaptcha.detect_key(html)

            if captcha_key:
                self.captcha = recaptcha
                response = recaptcha.challenge(captcha_key, html)
                inputs["g-recaptcha-response"] = response

            else:
                self.log_error(self._("ReCaptcha key not found"))
                self.fail_login(self._("ReCaptcha key not found"))

        html = self.load(url, post=inputs)

        json_data = json.loads(html)

        if json_data.get("state") != "1":
            self.log_error(json_data["msg"])
            self.fail_login()

    @property
    def logged(self):
        """
        Checks if user is still logged in
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

            self.log_debug("Reached login timeout for user `%s`" % self.user)
            return False
        else:
            return True

    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """

    def check_status(self):
        pass

    def retry_captcha(self, attempts=10, wait=1, msg="Max captcha retries reached"):
        self.captcha.invalid()
        self.fail_login(msg=self._("Invalid captcha"))
