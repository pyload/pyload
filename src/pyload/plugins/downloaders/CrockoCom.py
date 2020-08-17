# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class CrockoCom(SimpleDownloader):
    __name__ = "CrockoCom"
    __type__ = "downloader"
    __version__ = "0.27"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?(crocko|easy-share)\.com/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Crocko downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<span class="fz24">Download:\s*<strong>(?P<N>.*)'
    SIZE_PATTERN = r'<span class="tip1"><span class="inner">(?P<S>.+?)</span></span>'
    OFFLINE_PATTERN = r"<h1>Sorry,<br />the page you\'re looking for <br />isn\'t here.</h1>|File not found"

    CAPTCHA_PATTERN = r"u='(/file_contents/captcha/\w+)';\s*w='(\d+)';"

    FORM_PATTERN = r'<form  method="post" action="(.+?)">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="?([^" ]+)"? value="?([^" ]+)"?.*?>'

    NAME_REPLACEMENTS = [(r"<.*?>", "")]

    def handle_free(self, pyfile):
        if "You need Premium membership to download this file." in self.data:
            self.fail(self._("You need Premium membership to download this file"))

        for _ in range(5):
            m = re.search(self.CAPTCHA_PATTERN, self.data)
            if m is not None:
                url = urllib.parse.urljoin("http://crocko.com/", m.group(1))
                self.wait(m.group(2))
                self.data = self.load(url)
            else:
                break

        m = re.search(self.FORM_PATTERN, self.data, re.S)
        if m is None:
            self.error(self._("FORM_PATTERN not found"))

        action, form = m.groups()
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        self.captcha = ReCaptcha(pyfile)

        (
            inputs["recaptcha_response_field"],
            inputs["recaptcha_challenge_field"],
        ) = self.captcha.challenge()
        self.download(action, post=inputs)

        if self.scan_download({"captcha": self.captcha.KEY_V1_PATTERN}):
            self.retry_captcha()
