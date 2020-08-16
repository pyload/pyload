# -*- coding: utf-8 -*-

import re

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class UgouploadNet(SimpleDownloader):
    __name__ = "UgouploadNet"
    __type__ = "downloader"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www)?\.ugoupload\.net/\w{4}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """ugoupload.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<div class="heading-1 animated".*>(.+?)</div>'
    SIZE_PATTERN = r"\((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)<br/>"

    WAIT_PATTERN = r"var seconds = (\d+);"
    LINK_FREE_PATTERN = r"<a class='btn btn-free' href='(.+?)'"

    RECAPTCHA_KEY = "6LeuAc4SAAAAAOSry8eo2xW64K1sjHEKsQ5CaS10"

    def setup(self):
        self.resume_download = False
        self.multi_dl = False

    def handle_free(self, pyfile):
        if self.req.code == 404:
            self.offline()

        self.check_errors()

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            recaptcha = ReCaptcha(self)
            response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

            self.download(
                m.group(1),
                post={
                    "recaptcha_challenge_field": challenge,
                    "recaptcha_response_field": response,
                    "submit": "Submit",
                    "submitted": "1",
                    "d": "1",
                },
            )
