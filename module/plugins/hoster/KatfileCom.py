# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster
from ..internal.misc import parse_time
from ..captcha.SolveMedia import SolveMedia


class KatfileCom(SimpleHoster):
    __name__ = "KatfileCom"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?katfile\.com/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """katfile.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'>File Name: .+?>(?P<N>.+?)<'
    SIZE_PATTERN = r'>File Size: .+?>(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'

    OFFLINE_PATTERN = r'alt="file not found"'

    WAIT_PATTERN = r'var estimated_time = (\d+);'
    LINK_PATTERN = r'<a href="(.+?)" id="dlink">'

    COOKIES = [("katfile.com", "lang", "english")]

    def setup(self):
        self.multiDL = False
        self.chunk_limit = 1

    def check_errors(self):
        m = re.search(r'>Please wait (.+?) till next download<', self.data)
        if m is not None:
            self.retry(wait=parse_time(m.group(1)))

        SimpleHoster.check_errors(self)

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('id="btn_download"')
        if inputs is None:
            self.error(_("Form 1 not found"))

        inputs.pop('method_premium', None)

        self.data = self.load(pyfile.url, post=inputs)

        url, inputs = self.parse_html_form('name="F1"')
        if inputs is None:
            self.error(_("Form 2 not found"))

        self.check_errors()

        solvemedia = SolveMedia(self.pyfile)
        captcha_key = solvemedia.detect_key()

        if captcha_key:
            self.captcha = solvemedia
            response, challenge = solvemedia.challenge(captcha_key)
            inputs['adcopy_challenge'] = challenge
            inputs['adcopy_response'] = response

        else:
            self.error(_("Captcha not found"))

        self.data = self.load(pyfile.url, post=inputs)

        if ">Wrong captcha<" in self.data:
            self.retry_captcha()

        self.captcha.correct()

        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
