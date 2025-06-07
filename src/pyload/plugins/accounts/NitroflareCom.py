# -*- coding: utf-8 -*-
import json
import time

from pyload.core.datatypes.pyfile import PyFile

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.account import BaseAccount


class NitroflareCom(BaseAccount):
    __name__ = "NitroflareCom"
    __type__ = "account"
    __version__ = "0.22"
    __status__ = "testing"

    __description__ = """Nitroflare.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    RECAPTCHA_KEY = "6Lenx_USAAAAAF5L1pmTWvWcH73dipAEzNnmNLgy"

    # See https://nitroflare.com/member?s=general-api
    API_URL = "https://nitroflare.com/api/v2/"

    def api_request(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def grab_info(self, user, password, data):
        validuntil = -1
        trafficleft = None
        premium = False

        api_data = self.api_request("getKeyInfo", user=user, premiumKey=password)

        if api_data["type"] == "success":
            trafficleft = self.parse_traffic(api_data["result"]["trafficLeft"], "byte")
            premium = api_data["result"]["status"] == "active"

            if premium:
                validuntil = time.mktime(
                    time.strptime(api_data["result"]["expiryDate"], "%Y-%m-%d %H:%M:%S")
                )

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        api_data = self.api_request("getKeyInfo", user=user, premiumKey=password)

        if api_data["type"] != "success":
            error_code = api_data["code"]

            if error_code != 12:
                self.log_error(api_data["message"])
                self.fail_login()

            else:
                # dummy pyfile
                pyfile = PyFile(self.pyload.files, -1, "https://nitroflare.com", "https://nitroflare.com", 0, 0, "", self.classname, -1, -1)
                pyfile.plugin = self

                self.captcha = ReCaptcha(pyfile)
                response = self.captcha.challenge(self.RECAPTCHA_KEY, version="2js", secure_token=False)

                api_response = self.load(
                    self.API_URL + "solveCaptcha",
                    get={"user": user},
                    post={"response": response}
                )

                if api_response != "passed":
                    self.log_error(self._("Recaptcha verification failed"))
                    self.fail_login(self._("Recaptcha verification failed"))

    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """
    def check_status(self):
        pass

    def retry_captcha(self, attempts=10, wait=1, msg="Max captcha retries reached"):
        self.captcha.invalid()
        self.fail_login(msg=self._("Invalid captcha"))
