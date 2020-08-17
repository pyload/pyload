# -*- coding: utf-8 -*-

import re

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class CatShareNet(SimpleDownloader):
    __name__ = "CatShareNet"
    __type__ = "downloader"
    __version__ = "0.22"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?catshare\.net/\w{15,16}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """CatShare.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("z00nx", "z00nx0@gmail.com"),
        ("prOq", None),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = r'(?:<div class="col-sm-8 col-xs-12 text-left">\s*<h3>|<title>)(?P<N>.+)(?:</h3>| \()'
    SIZE_PATTERN = r'(?:<div class="col-sm-4 col-xs-12 text-right">\s*<h3>|<title>.+?\()(?P<S>[\d.,]+) (?P<U>[\w^_]+)(?:</h3>|\))'

    OFFLINE_PATTERN = r'<div class="alert alert-error"'

    IP_BLOCKED_PATTERN = r">Nasz serwis wykrył że Twój adres IP nie pochodzi z Polski.<"
    WAIT_PATTERN = r"var\scount\s=\s(\d+);"

    LINK_FREE_PATTERN = r'<form action="(.+?)" method="GET">'
    LINK_PREMIUM_PATTERN = r'<form action="(.+?)" method="GET">'

    def setup(self):
        self.multi_dl = self.premium
        self.resume_download = True

    def handle_free(self, pyfile):
        self.captcha = ReCaptcha(pyfile)

        response, challenge = self.captcha.challenge()
        self.data = self.load(
            pyfile.url,
            post={
                "recaptcha_challenge_field": challenge,
                "recaptcha_response_field": response,
            },
        )

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

    def handle_premium(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
