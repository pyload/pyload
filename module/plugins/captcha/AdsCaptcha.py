# -*- coding: utf-8 -*-

import random
import re

from ..internal.CaptchaService import CaptchaService


class AdsCaptcha(CaptchaService):
    __name__ = "AdsCaptcha"
    __type__ = "captcha"
    __version__ = "0.14"
    __status__ = "testing"

    __description__ = """AdsCaptcha captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad Team", "admin@pyload.org")]

    CAPTCHAID_PATTERN = r'api\.adscaptcha\.com/Get\.aspx\?.*?CaptchaId=(\d+)'
    PUBLICKEY_PATTERN = r'api\.adscaptcha\.com/Get\.aspx\?.*?PublicKey=([\w\-]+)'

    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.PUBLICKEY_PATTERN, html)
        n = re.search(self.CAPTCHAID_PATTERN, html)
        if m and n:
            #: Key is the tuple(PublicKey, CaptchaId)
            self.key = (m.group(1).strip(), n.group(1).strip())
            self.log_debug("Key: %s | ID: %s" % self.key)
            return self.key
        else:
            self.log_debug("Key or id pattern not found")
            return None

    def challenge(self, key=None, data=None):
        PublicKey, CaptchaId = key or self.retrieve_key(data)

        html = self.pyfile.plugin.load("http://api.adscaptcha.com/Get.aspx",
                                       get={'CaptchaId': CaptchaId,
                                            'PublicKey': PublicKey})
        try:
            challenge = re.search("challenge: '(.+?)',", html).group(1)
            server = re.search("server: '(.+?)',", html).group(1)

        except AttributeError:
            self.fail(_("AdsCaptcha challenge pattern not found"))

        self.log_debug("Challenge: %s" % challenge)

        return self.result(server, challenge), challenge

    def result(self, server, challenge):
        result = self.decrypt("%sChallenge.aspx" % server,
                              get={'cid': challenge, 'dummy': random.random()},
                              cookies=True,
                              input_type="jpg")
        return result
