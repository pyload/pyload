# -*- coding: utf-8 -*-

import json
import re

from pyload.core.datatypes.pyfile import PyFile
from pyload.core.network.http.exceptions import BadHeader

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.account import BaseAccount
from ..base.captcha import BaseCaptcha


class Keep2ShareCc(BaseAccount):
    __name__ = "Keep2ShareCc"
    __type__ = "account"
    __version__ = "0.21"
    __status__ = "testing"

    __description__ = """Keep2Share.cc account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("aeronaut", "aeronaut@pianoguy.de"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    RECAPTCHA_KEY = "6LcOsNIaAAAAABzCMnQw7u0u8zd1mrqY6ibFtto8"

    API_URL = "https://keep2share.cc/api/v2/"
    #: See https://keep2share.github.io/api/ https://github.com/keep2share/api

    def api_request(self, method, **kwargs):
        html = self.load(self.API_URL + method, post=json.dumps(kwargs))
        return json.loads(html)

    def grab_info(self, user, password, data):
        json_data = self.api_request("AccountInfo", auth_token=data["token"])

        return {
            "validuntil": json_data["account_expires"],
            "trafficleft": json_data["available_traffic"],
            "premium": True if json_data["account_expires"] else False,
        }

    def signin(self, user, password, data):
        if "token" in data:
            try:
                json_data = self.api_request("test", auth_token=data["token"])

            except BadHeader as exc:
                if exc.code == 403:  #: Session expired
                    pass

                else:
                    raise
            else:
                self.skip_login()

        try:
            json_data = self.api_request("login", username=user, password=password)

        except BadHeader as exc:
            if exc.code == 406:  #: Captcha needed
                # dummy pyfile
                pyfile = PyFile(
                    self.pyload.files,
                    -1,
                    "https://k2s.cc",
                    "https://k2s.cc",
                    0,
                    0,
                    "",
                    self.classname,
                    -1,
                    -1,
                )
                pyfile.plugin = self

                errors = [
                    json.loads(m.group(0)).get("errorCode", 0)
                    for m in re.finditer(r"{[^}]+}", exc.content)
                ]
                if 33 in errors:  #: ERROR_RE_CAPTCHA_REQUIRED
                    #: Recaptcha
                    self.captcha = ReCaptcha(pyfile)
                    for i in range(10):
                        json_data = self.api_request("RequestReCaptcha")
                        if json_data["code"] != 200:
                            self.log_error(_("Request reCAPTCHA API failed"))
                            self.fail_login(_("Request reCAPTCHA API failed"))

                        re_captcha_response = self.captcha.challenge(
                            self.RECAPTCHA_KEY, version="2js", secure_token=False
                        )
                        try:
                            json_data = self.api_request(
                                "login",
                                username=user,
                                password=password,
                                re_captcha_challenge=json_data["challenge"],
                                re_captcha_response=re_captcha_response,
                            )

                        except BadHeader as exc:
                            if exc.code == 406:
                                errors = [
                                    json.loads(m.group(0)).get("errorCode", 0)
                                    for m in re.finditer(r"{[^}]+}", exc.content)
                                ]
                                if 31 in errors:  #: ERROR_CAPTCHA_INVALID
                                    self.captcha.invalid()
                                    continue

                                else:
                                    self.log_error(exc.content)
                                    self.fail_login(exc.content)

                            else:
                                self.log_error(exc.content)
                                self.fail_login(exc.content)

                        else:
                            self.captcha.correct()
                            data["token"] = json_data["auth_token"]
                            break

                    else:
                        self.log_error(_("Max captcha retries reached"))
                        self.fail_login(_("Max captcha retries reached"))

                elif 30 in errors:  #: ERROR_CAPTCHA_REQUIRED
                    #: Normal captcha
                    self.captcha = BaseCaptcha(pyfile)
                    for i in range(10):
                        json_data = self.api_request("RequestCaptcha")
                        if json_data["code"] != 200:
                            self.log_error(self._("Request captcha API failed"))
                            self.fail_login(self._("Request captcha API failed"))

                        captcha_response = self.captcha.decrypt(
                            json_data["captcha_url"]
                        )
                        try:
                            json_data = self.api_request(
                                "login",
                                username=user,
                                password=password,
                                captcha_challenge=json_data["challenge"],
                                captcha_response=captcha_response,
                            )

                        except BadHeader as exc:
                            if exc.code == 406:
                                errors = [
                                    json.loads(m.group(0)).get("errorCode", 0)
                                    for m in re.finditer(r"{[^}]+}", exc.content)
                                ]
                                if 31 in errors:  #: ERROR_CAPTCHA_INVALID
                                    self.captcha.invalid()
                                    continue

                                else:
                                    self.log_error(exc.content)
                                    self.fail_login(exc.content)

                            else:
                                self.log_error(exc.content)
                                self.fail_login(exc.content)

                        else:
                            self.captcha.correct()
                            data["token"] = json_data["auth_token"]
                            break

                    else:
                        self.log_error(self._("Max captcha retries reached"))
                        self.fail_login(self._("Max captcha retries reached"))

                else:
                    self.log_error(exc.content)
                    self.fail_login(exc.content)

            else:
                self.log_error(exc.content)
                self.fail_login(exc.content)

        else:
            #: No captcha
            data["token"] = json_data["auth_token"]

    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """

    def check_status(self):
        pass

    def retry_captcha(self, attempts=10, wait=1, msg="Max captcha retries reached"):
        self.captcha.invalid()
        self.fail_login(msg=self._("Invalid captcha"))
