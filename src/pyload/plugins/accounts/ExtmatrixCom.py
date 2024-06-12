# -*- coding: utf-8 -*-

import re
import time
import urllib.parse

from pyload.core.datatypes.pyfile import PyFile

from ..base.account import BaseAccount
from ..base.captcha import BaseCaptcha


class ExtmatrixCom(BaseAccount):
    __name__ = "ExtmatrixCom"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = """Extmatrix.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    VALID_UNTIL_PATTERN = r">Premium End:</td>\s*<td>([\d-]+)</td>"

    def grab_info(self, user, password, data):
        html = self.load("https://www.extmatrix.com")

        premium = ">Premium Member<" in html

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            validuntil = time.mktime(
                time.strptime(m.group(1) + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )

        else:
            self.log_error(self._("VALID_UNTIL_PATTERN not found"))
            validuntil = None

        return {"validuntil": validuntil, "trafficleft": None, "premium": premium}

    def signin(self, user, password, data):
        html = self.load("https://www.extmatrix.com/login.php")
        if 'href="./logout.php"' in html:
            self.skip_login()

        # dummy pyfile
        pyfile = PyFile(
            self.pyload.files,
            -1,
            "https://www.extmatrix.com",
            "https://www.extmatrix.com",
            0,
            0,
            "",
            self.classname,
            -1,
            -1,
        )
        pyfile.plugin = self

        for i in range(5):
            m = re.search(r'<img src="(.+?captcha\.php.+?)"', html)
            if m is None:
                self.fail_login("Captcha pattern not found")

            captcha_url = urllib.parse.urljoin("https://www.extmatrix.com/", m.group(1))
            self.captcha = BaseCaptcha(pyfile)
            captcha_response = self.captcha.decrypt(captcha_url)

            html = self.load(
                "https://www.extmatrix.com/login.php",
                post={
                    "user": user,
                    "pass": password,
                    "submit": "Login",
                    "task": "dologin",
                    "return=": "./members/myfiles.php",
                    "captcha": captcha_response,
                },
            )

            if "Incorrect captcha code" in html:
                self.captcha.invalid()

            else:
                self.captcha.correct()
                break

        else:
            self.fail_login(self._("Max captcha retries reached"))

        html = self.load("https://www.extmatrix.com")
        if 'href="./logout.php"' not in html:
            self.fail_login()

    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """

    def check_status(self):
        pass

    def retry_captcha(self, attempts=10, wait=1, msg="Max captcha retries reached"):
        self.captcha.invalid()
        self.fail_login(msg=self._("Invalid captcha"))
