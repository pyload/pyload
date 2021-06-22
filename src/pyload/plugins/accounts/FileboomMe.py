# -*- coding: utf-8 -*-

import json
import re

from pyload.core.datatypes.pyfile import PyFile
from pyload.core.network.HTTPRequest import BadHeader
from pyload.core.network.request_factory import get_url

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.account import BaseAccount
from ..base.captcha import BaseCaptcha


class FileboomMe(BaseAccount):
    __name__ = "FileboomMe"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = """Fileboom.me account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    RECAPTCHA_KEY = "6LcYcN0SAAAAABtMlxKj7X0hRxOY8_2U86kI1vbb"

    API_URL = "https://fileboom.me/api/v2/"
    #: Actually this is Keep2ShareCc API, see https://keep2share.github.io/api/ https://github.com/keep2share/api

    @classmethod
    def api_request(cls, method, **kwargs):
        html = get_url(cls.API_URL + method,
                       post=json.dumps(kwargs))
        return json.loads(html)

    def grab_info(self, user, password, data):
        json_data = self.api_request("AccountInfo", auth_token=data['token'])

        return {'validuntil': json_data['account_expires'],
                'trafficleft': json_data['available_traffic'],
                'premium': True if json_data['account_expires'] else False}

    def signin(self, user, password, data):
        if 'token' in data:
            try:
                json_data = self.api_request("test", auth_token=data['token'])

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
                pyfile = PyFile(self.pyload.files, -1, "https://fileboom.me", "https://fileboom.me", 0, 0, "", self.classname, -1, -1)
                pyfile.plugin = self

                errors = [json.loads(m.group(0)).get('errorCode', 0) for m in re.finditer(r'{[^}]+}', exc.content)]
                if 33 in errors:  #: ERROR_RE_CAPTCHA_REQUIRED
                    #: Recaptcha
                    self.captcha = ReCaptcha(pyfile)
                    for i in range(10):
                        json_data = self.api_request("RequestReCaptcha")
                        if json_data['code'] != 200:
                            self.log_error(_("Request reCAPTCHA API failed"))
                            self.fail_login(_("Request reCAPTCHA API failed"))

                        re_captcha_response, _ = self.captcha.challenge(self.RECAPTCHA_KEY, version="2js", secure_token=False)
                        try:
                            json_data = self.api_request("login",
                                                          username=user,
                                                          password=password,
                                                          re_captcha_challenge=json_data['challenge'],
                                                          re_captcha_response=re_captcha_response)

                        except BadHeader as exc:
                            if exc.code == 406:
                                errors = [json.loads(m.group(0)).get('errorCode', 0) for m in re.finditer(r'{[^}]+}', exc.content)]
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
                            data['token'] = json_data['auth_token']
                            break

                    else:
                        self.log_error(_("Max captcha retries reached"))
                        self.fail_login(_("Max captcha retries reached"))

                elif 30 in errors:  #: ERROR_CAPTCHA_REQUIRED
                    #: Normal captcha
                    self.captcha = BaseCaptcha(pyfile)
                    for i in range(10):
                        json_data = self.api_request("RequestCaptcha")
                        if json_data['code'] != 200:
                            self.log_error(self._("Request captcha API failed"))
                            self.fail_login(self._("Request captcha API failed"))

                        captcha_response = self.captcha.decrypt(json_data['captcha_url'])
                        try:
                            json_data = self.api_request("login",
                                                          username=user,
                                                          password=password,
                                                          captcha_challenge=json_data['challenge'],
                                                          captcha_response=captcha_response)

                        except BadHeader as exc:
                            if exc.code == 406:
                                errors = [json.loads(m.group(0)).get('errorCode', 0) for m in re.finditer(r'{[^}]+}', exc.content)]
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
                            data['token'] = json_data['auth_token']
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
            data['token'] = json_data['auth_token']

    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """
    def check_status(self):
        pass

    def retry_captcha(self, attemps=10, wait=1, msg="Max captcha retries reached"):
        self.captcha.invalid()
        self.fail_login(msg=self._("Invalid captcha"))
