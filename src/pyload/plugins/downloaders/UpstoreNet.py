# -*- coding: utf-8 -*-

import json
import re

from ..anticaptchas.HCaptcha import HCaptcha
from ..base.simple_downloader import SimpleDownloader


class UpstoreNet(SimpleDownloader):
    __name__ = "UpstoreNet"
    __type__ = "downloader"
    __version__ = "0.18"
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

    DL_LIMIT_PATTERN = r"Please wait .+? before downloading next"
    WAIT_PATTERN = r"var sec = (\d+)"

    COOKIES = [("upstore.net", "lang", "en")]

    def handle_free(self, pyfile):
        #: STAGE 1: get link to continue
        self.data = self.load(pyfile.url,
                              post={'hash': self.info['pattern']['ID'],
                                    'free': 'Slow download'})

        #: STAGE 2: solve captcha and wait
        #: First get the infos we need: self.captcha key and wait time
        m = re.search(self.WAIT_PATTERN, self.data)
        if m is None:
            self.error(self._("Wait pattern not found"))

        #: prepare the waiting
        wait_time = int(m.group(1))
        self.set_wait(wait_time)

        #: then, handle the captcha
        hcaptcha = HCaptcha(self.pyfile)

        captcha_key = hcaptcha.detect_key()
        if captcha_key is None:
            self.fail(self._("captcha key not found"))

        self.captcha = hcaptcha

        post_data = {'hash': self.info['pattern']['ID'],
                     'free': 'Get download link',
                     'antispam': "spam",
                     'kpw': "spam"}
        post_data['h-captcha-response'] = post_data['g-recaptcha-response'] = hcaptcha.challenge(captcha_key)

        #: then, do the waiting
        self.wait()

        self.data = self.load(pyfile.url,
                              post=post_data,
                              ref=pyfile.url)

        #: check whether the captcha was wrong
        if "Captcha check failed" in self.data:
            self.captcha.invalid()

        else:
            self.captcha.correct()

        # STAGE 3: get direct link or wait time
        self.check_errors()

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

    def handle_premium(self, pyfile):
        self.data = self.load("https://upstore.net/load/premium",
                              post={'hash': self.info['pattern']['ID'],
                                    'antispam': "spam",
                                    'js': "1"})
        json_data = json.loads(self.data)
        self.link = json_data['ok']
