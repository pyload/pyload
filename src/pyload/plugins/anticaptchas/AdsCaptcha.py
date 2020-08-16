# -*- coding: utf-8 -*-
import random
import re

from ..base.captcha_service import CaptchaService


class AdsCaptcha(CaptchaService):
    __name__ = "AdsCaptcha"
    __type__ = "anticaptcha"
    __version__ = "0.14"
    __status__ = "testing"

    __description__ = """AdsCaptcha captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad team", "admin@pyload.net")]

    CAPTCHAID_PATTERN = r"api\.adscaptcha\.com/Get\.aspx\?.*?CaptchaId=(\d+)"
    PUBLICKEY_PATTERN = r"api\.adscaptcha\.com/Get\.aspx\?.*?PublicKey=([\w\-]+)"

    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.PUBLICKEY_PATTERN, html)
        n = re.search(self.CAPTCHAID_PATTERN, html)
        if m and n:
            #: Key is the tuple(PublicKey, CaptchaId)
            key = m.group(1).strip()
            id = n.group(1).strip()
            self.key = (key, id)
            self.log_debug(f"Key: {key} | ID: {id}")
            return self.key
        else:
            self.log_debug("Key or id pattern not found")
            return None

    def challenge(self, key=None, data=None):
        PublicKey, CaptchaId = key or self.retrieve_key(data)

        html = self.pyfile.plugin.load(
            "http://api.adscaptcha.com/Get.aspx",
            get={"CaptchaId": CaptchaId, "PublicKey": PublicKey},
        )
        try:
            challenge = re.search("challenge: '(.+?)',", html).group(1)
            server = re.search("server: '(.+?)',", html).group(1)

        except AttributeError:
            self.fail(self._("AdsCaptcha challenge pattern not found"))

        self.log_debug(f"Challenge: {challenge}")

        return self.result(server, challenge), challenge

    def result(self, server, challenge):
        result = self.decrypt(
            "{}Challenge.aspx".format(server),
            get={"cid": challenge, "dummy": random.random()},
            cookies=True,
            input_type="jpg",
        )
        return result
