# -*- coding: utf-8 -*-


from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class UploadgigCom(SimpleDownloader):
    __name__ = "UploadgigCom"
    __type__ = "downloader"
    __version__ = "0.04"
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

    LOGIN_PREMIUM = (
        True  #: Free download is not possible because they blocked noscript ReCaptcha
    )

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('id="dl_captcha_form"')
        if inputs is None:
            self.error(self._("Free download form not found"))

        recaptcha = ReCaptcha(pyfile)

        captcha_key = recaptcha.detect_key()
        if captcha_key is None:
            self.error(self._("ReCaptcha key not found"))

        self.captcha = recaptcha
        response, challenge = recaptcha.challenge(captcha_key)

        inputs["g-recaptcha-response"] = response
        self.data = self.load(self.fixurl(url), post=inputs)
