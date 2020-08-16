# -*- coding: utf-8 -*-

import re

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class UpstoreNet(SimpleDownloader):
    __name__ = "UpstoreNet"
    __type__ = "downloader"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:upstore\.net|upsto\.re)/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Upstore.Net File Download Hoster"""
    __license__ = "GPLv3"
    __authors__ = [
        ("igel", "igelkun@myopera.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    INFO_PATTERN = r'<div class="comment">.*?</div>\s*\n<h2 style="margin:0">(?P<N>.*?)</h2>\s*\n<div class="comment">\s*\n\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'<span class="error">File (?:not found|was deleted).*</span>'

    PREMIUM_ONLY_PATTERN = r"available only for Premium"
    LINK_FREE_PATTERN = r'<a href="(https?://.*?)" target="_blank"><b>'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://upstore.net/\g<ID>")]

    DL_LIMIT_PATTERN = r"Please wait (.+?) before downloading next"
    WAIT_PATTERN = r"var sec = (\d+)"
    CHASH_PATTERN = r'<input type="hidden" name="hash" value="(.+?)">'

    COOKIES = [("upstore.net", "lang", "en")]

    def handle_free(self, pyfile):
        #: STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.data)
        if m is None:
            self.error(self._("CHASH_PATTERN not found"))

        chash = m.group(1)
        self.log_debug("Read hash " + chash)

        #: Continue to stage2
        post_data = {"hash": chash, "free": "Slow download"}
        self.data = self.load(pyfile.url, post=post_data)

        #: STAGE 2: solve captcha and wait
        #: First get the infos we need: self.captcha key and wait time
        self.captcha = ReCaptcha(pyfile)

        #: Try the captcha 5 times
        for i in range(5):
            m = re.search(self.WAIT_PATTERN, self.data)
            if m is None:
                self.error(self._("Wait pattern not found"))

            #: then, do the waiting
            wait_time = int(m.group(1))
            self.wait(wait_time)

            #: then, handle the captcha
            response, challenge = self.captcha.challenge()
            post_data.update(
                {
                    "recaptcha_challenge_field": challenge,
                    "recaptcha_response_field": response,
                }
            )

            self.data = self.load(pyfile.url, post=post_data)

            # check whether the captcha was wrong
            if "Wrong captcha" in self.data:
                self.captcha.invalid()

            else:
                self.captcha.correct()
                break

        else:
            self.fail(self._("Max captcha retries reached"))

        # STAGE 3: get direct link or wait time
        self.check_errors()

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
