# -*- coding: utf-8 -*-

import re

from pyload.core.network.exceptions import Fail

from ..base.captcha_service import CaptchaService


class SolveMedia(CaptchaService):
    __name__ = "SolveMedia"
    __type__ = "anticaptcha"
    __version__ = "0.22"
    __status__ = "testing"

    __description__ = """SolveMedia captcha service plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad team", "admin@pyload.net")]

    KEY_PATTERN = (
        r'api(?:-secure)?\.solvemedia\.com/papi/challenge\.(?:no)?script\?k=(.+?)["\']'
    )

    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_PATTERN, html)
        if m is not None:
            self.key = m.group(1).strip()
            self.log_debug(f"Key: {self.key}")
            return self.key
        else:
            self.log_debug("Key pattern not found")
            return None

    def challenge(self, key=None, data=None):
        key = key or self.retrieve_key(data)

        html = self.pyfile.plugin.load(
            "http://api.solvemedia.com/papi/challenge.noscript", get={"k": key}
        )

        for i in range(1, 11):
            try:
                magic = re.search(r'name="magic" value="(.+?)"', html).group(1)

            except AttributeError:
                self.log_warning(self._("Magic pattern not found"))
                magic = None

            try:
                challenge = re.search(
                    r'<input type=hidden name="adcopy_challenge" id="adcopy_challenge" value="(.+?)">',
                    html,
                ).group(1)

            except AttributeError:
                self.fail(self._("SolveMedia challenge pattern not found"))

            else:
                self.log_debug(f"Challenge: {challenge}")

            try:
                result = self.result("http://api.solvemedia.com/papi/media", challenge)

            except Fail as exc:
                self.log_warning(
                    exc,
                    exc_info=self.pyload.debug > 1,
                    stack_info=self.pyload.debug > 2,
                )
                self.pyfile.plugin.captcha.invalid()
                result = None

            html = self.pyfile.plugin.load(
                "http://api.solvemedia.com/papi/verify.noscript",
                post={
                    "adcopy_response": result,
                    "k": key,
                    "l": "en",
                    "t": "img",
                    "s": "standard",
                    "magic": magic,
                    "adcopy_challenge": challenge,
                    "ref": self.pyfile.url,
                },
            )
            try:
                redirect = re.search(r'URL=(.+?)">', html).group(1)

            except AttributeError:
                self.fail(self._("SolveMedia verify pattern not found"))

            else:
                if "error" in html:
                    self.log_warning(self._("Captcha code was invalid"))
                    self.log_debug(f"Retry #{i}")
                    html = self.pyfile.plugin.load(redirect)
                else:
                    break

        else:
            self.fail(self._("SolveMedia max retries exceeded"))

        return result, challenge

    def result(self, server, challenge):
        result = self.decrypt(
            server, get={"c": challenge}, cookies=True, input_type="gif"
        )
        return result
