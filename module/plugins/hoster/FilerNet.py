# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import re

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.SimpleHoster import SimpleHoster


class FilerNet(SimpleHoster):
    __name__ = "FilerNet"
    __type__ = "hoster"
    __version__ = "0.29"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?filer\.net/get/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Filer.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    INFO_PATTERN = r'<h1 class="page-header">Free Download (?P<N>\S+) <small>(?P<S>[\w.]+) (?P<U>[\w^_]+)</small></h1>'

    OFFLINE_PATTERN = r'Nicht gefunden'
    TEMP_OFFLINE_PATTERN = r'Leider sind alle kostenlosen Download-Slots belegt'

    WAIT_PATTERN = r'var count = (\d+);'

    LINK_PATTERN = r'href="([^"]+)">Get download</a>'

    def handle_free(self, pyfile):
        inputs = self.parse_html_form(input_names={'token': re.compile(r'.+')})[1]
        if inputs is None or 'token' not in inputs:
            self.retry()

        self.data = self.load(pyfile.url, post={'token': inputs['token']})

        inputs = self.parse_html_form(input_names={'hash': re.compile(r'.+')})[1]
        if inputs is None or 'hash' not in inputs:
            self.error(_("Unable to detect hash"))

        self.captcha = ReCaptcha(pyfile)
        response, challenge = self.captcha.challenge()

        self.download(pyfile.url,
                      post={'g-recaptcha-response': response,
                            'hash': inputs['hash']})

    def check_download(self):
        if self.scan_download({'html': re.compile(r'\A\s*<!DOCTYPE html')}) == "html":
            with open(self.last_download, "r") as f:
                self.data = f.read()
            os.remove(self.last_download)
            if re.search(self.TEMP_OFFLINE_PATTERN, self.data) is not None:
                self.temp_offline()

            else:
                return SimpleHoster.check_download(self)

        else:
            return SimpleHoster.check_download(self)
