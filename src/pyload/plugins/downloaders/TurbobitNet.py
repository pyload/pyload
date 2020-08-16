# -*- coding: utf-8 -*-

import re

import pycurl
from pyload.core.utils.misc import eval_js

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class TurbobitNet(SimpleDownloader):
    __name__ = "TurbobitNet"
    __type__ = "downloader"
    __version__ = "0.33"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?turbobit\.net/(?:download/free/)?(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Turbobit.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("prOq", None),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://turbobit.net/\g<ID>.html")]

    COOKIES = [("turbobit.net", "user_lang", "en")]

    INFO_PATTERN = (
        r"<title>\s*Download file (?P<N>.+?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)"
    )
    OFFLINE_PATTERN = r"<h2>File Not Found</h2>|html\(\'File (?:was )?not found"
    TEMP_OFFLINE_PATTERN = r""

    LINK_FREE_PATTERN = r'(/download/redirect/[^"\']+)'
    LINK_PREMIUM_PATTERN = r'<a href=[\'"](.+?/download/redirect/[^"\']+)'

    LIMIT_WAIT_PATTERN = r"<div id=\'timeout\'>(\d+)<"

    def handle_free(self, pyfile):
        self.free_url = "http://turbobit.net/download/free/{}".format(
            self.info["pattern"]["ID"]
        )
        self.data = self.load(self.free_url)

        m = re.search(self.LIMIT_WAIT_PATTERN, self.data)
        if m is not None:
            self.retry(wait=m.group(1))

        self.solve_captcha()

        m = re.search(r"minLimit : (.+?),", self.data)
        if m is None:
            self.fail(self._("minLimit pattern not found"))

        wait_time = eval_js(m.group(1))
        self.wait(wait_time)

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.data = self.load(
            "http://turbobit.net/download/getLinkTimeout/{}".format(
                self.info["pattern"]["ID"]
            ),
            ref=self.free_url,
        )
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        if "/download/started/" in self.data:
            self.data = self.load(
                "http://turbobit.net/download/started/{}".format(
                    self.info["pattern"]["ID"]
                )
            )

            m = re.search(self.LINK_FREE_PATTERN, self.data)
            if m is not None:
                self.link = "http://turbobit.net{}".format(m.group(1))

    def solve_captcha(self):
        action, inputs = self.parse_html_form("action='#'")
        if not inputs:
            self.fail(self._("Captcha form not found"))

        if inputs["captcha_type"] == "recaptcha2":
            self.captcha = ReCaptcha(self.pyfile)
            inputs["g-recaptcha-response"], challenge = self.captcha.challenge()

        else:
            self.fail(self._("Unknown captcha type"))

        self.data = self.load(self.free_url, post=inputs)

    def handle_premium(self, pyfile):
        m = re.search(self.LINK_PREMIUM_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
