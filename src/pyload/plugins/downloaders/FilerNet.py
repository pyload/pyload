# -*- coding: utf-8 -*-
import os
import re

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class FilerNet(SimpleDownloader):
    __name__ = "FilerNet"
    __type__ = "downloader"
    __version__ = "0.28"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filer\.net/get/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filer.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    INFO_PATTERN = r'<h1 class="page-header">Free Download (?P<N>\S+) <small>(?P<S>[\w.]+) (?P<U>[\w^_]+)</small></h1>'
    OFFLINE_PATTERN = r"Nicht gefunden"

    WAIT_PATTERN = r"var count = (\d+);"

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'href="([^"]+)">Get download</a>'

    def handle_free(self, pyfile):
        inputs = self.parse_html_form(input_names={"token": re.compile(r".+")})[1]
        if inputs is None or "token" not in inputs:
            self.retry()

        self.data = self.load(pyfile.url, post={"token": inputs["token"]})

        inputs = self.parse_html_form(input_names={"hash": re.compile(r".+")})[1]
        if inputs is None or "hash" not in inputs:
            self.error(self._("Unable to detect hash"))

        self.captcha = ReCaptcha(pyfile)
        response, challenge = self.captcha.challenge()

        #: Avoid 'Correct catcha'
        captcha_task = self.captcha.task
        self.captcha.task = None

        self.download(
            pyfile.url, post={"g-recaptcha-response": response, "hash": inputs["hash"]}
        )

        #: Restore the captcha task
        self.captcha.task = captcha_task

        if self.scan_download({"html": re.compile(r"\A\s*<!DOCTYPE html")}) == "html":
            self.log_warning(
                self._(
                    "There was HTML code in the downloaded file ({})...bad captcha? The download will be restarted"
                ).format(self.pyfile.name)
            )
            os.remove(self.last_download)
            self.retry_captcha()

        else:
            self.captcha.correct()
