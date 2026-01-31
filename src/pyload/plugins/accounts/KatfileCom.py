# -*- coding: utf-8 -*-

import urllib.parse

from pyload.core.datatypes.pyfile import PyFile

from ..anticaptchas.HCaptcha import HCaptcha
from ..base.xfs_account import XFSAccount
from ..helpers import parse_html_form, search_pattern


class KatfileCom(XFSAccount):
    __name__ = "KatfileCom"
    __type__ = "account"
    __version__ = "0.03"
    __status__ = "testing"

    __description__ = """Katfile.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "katfile.online"
    PLUGIN_URL = "https://katfile.online"

    PREMIUM_PATTERN = r"Extend Premium account"
    VALID_UNTIL_PATTERN = r"<TD>Premium Pro account expire</TD><TD><b>(.+?)<"
    TRAFFIC_LEFT_PATTERN = r"Traffic available today.*?<b>\s*(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?"

    def signin(self, user, password, data):
        self.data = self.load(self.LOGIN_URL, cookies=self.COOKIES)

        if search_pattern(self.LOGIN_SKIP_PATTERN, self.data):
            self.skip_login()

        action, inputs = parse_html_form('name="FL"', self.data)
        if not inputs:
            inputs = {"op": "login", "redirect": self.PLUGIN_URL}

        inputs.update({"login": user, "password": password})

        if action:
            url = urllib.parse.urljoin(self.LOGIN_URL, action)
        else:
            url = self.LOGIN_URL

        # dummy pyfile
        pyfile = PyFile(self.pyload.files, -1, self.PLUGIN_URL, self.PLUGIN_URL, 0, 0, "", self.classname, -1, -1)
        pyfile.plugin = self

        self.captcha = HCaptcha(pyfile)
        captcha_key = self.captcha.detect_key()
        if captcha_key:
            response = self.captcha.challenge(captcha_key)
            inputs.update({
                "h-captcha-response": response,
                "g-recaptcha-response": response
            })

        self.data = self.load(url, post=inputs, cookies=self.COOKIES)

        self.check_errors()


    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """

    def check_status(self):
        pass

    def retry_captcha(self, attempts=10, wait=1, msg="Max captcha retries reached"):
        self.captcha.invalid()
        self.fail_login(msg=self._("Invalid captcha"))
