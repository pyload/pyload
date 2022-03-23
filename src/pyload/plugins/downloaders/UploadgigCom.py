# -*- coding: utf-8 -*-

import json
import re

from pyload.core.utils.misc import eval_js

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class UploadgigCom(SimpleDownloader):
    __name__ = "UploadgigCom"
    __type__ = "downloader"
    __version__ = "0.10"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?uploadgig.com/file/download/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Uploadgig.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [("http://", "https://")]

    NAME_PATTERN = r'<span class="filename">(?P<N>.+?)<'
    SIZE_PATTERN = r'<span class="filesize">\[(?P<S>[\d.,]+) (?P<U>[\w^_]+)\]<'

    OFFLINE_PATTERN = r"File not found"

    def handle_free(self, pyfile):
        m = re.search(
            r"<script>window\[String\.fromCharCode\(window\['m'\+'ax_upload_limi'\+'t'\]\)\] = (.+?);</script>",
            self.data,
        )
        if m is None:
            self.error(self._("f pattern not found"))

        f = eval_js(m.group(1))

        url, inputs = self.parse_html_form('id="dl_captcha_form"')
        if inputs is None:
            self.error(self._("Free download form not found"))

        recaptcha = ReCaptcha(pyfile)

        captcha_key = recaptcha.detect_key()
        if captcha_key is None:
            self.error(self._("ReCaptcha key not found"))

        self.captcha = recaptcha
        response = recaptcha.challenge(captcha_key)

        inputs["g-recaptcha-response"] = response
        self.data = self.load(self.fixurl(url), post=inputs)

        if self.data == "m":
            self.log_warning(self._("Max downloads for this hour reached"))
            self.retry(wait=60 * 60)

        elif self.data in ("fl", "rfd"):
            self.fail(self._("File can be downloaded by premium users only"))

        elif self.data == "e":
            self.retry()

        elif self.data == "0":
            self.retry_captcha()

        else:
            try:
                res = json.loads(self.data)

            except ValueError:
                self.fail(self._("Illegal response from the server"))

            if any([_x not in res for _x in ("cd", "sp", "q", "id")]):
                self.fail(self._("Illegal response from the server"))

            self.wait(res["cd"])

            self.link = res["sp"] + "id=" + str(res["id"] - int(f)) + "&" + res["q"]
