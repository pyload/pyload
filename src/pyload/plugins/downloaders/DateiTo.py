# -*- coding: utf-8 -*-

import re

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class DateiTo(SimpleDownloader):
    __name__ = "DateiTo"
    __type__ = "downloader"
    __version__ = "0.14"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?datei\.to/datei/(?P<ID>\w+)\.html"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Datei.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'Dateiname:</td>\s*<td colspan="2"><strong>(?P<N>.*?)</'
    SIZE_PATTERN = r'Dateigr&ouml;&szlig;e:</td>\s*<td colspan="2">(?P<S>.*?)</'
    OFFLINE_PATTERN = r">Datei wurde nicht gefunden<|>Bitte wähle deine Datei aus... <"

    WAIT_PATTERN = r"countdown\({seconds: (\d+)"
    DOWNLOAD_PATTERN = r">Du lädst bereits eine Datei herunter"

    DATA_PATTERN = r'url: "(.*?)", data: "(.*?)",'

    def handle_free(self, pyfile):
        url = "http://datei.to/ajax/download.php"
        data = {"P": "I", "ID": self.info["pattern"]["ID"]}
        self.captcha = ReCaptcha(pyfile)

        for _ in range(3):
            self.log_debug("URL", url, "POST", data)
            self.data = self.load(url, post=data)
            self.check_errors()

            if url.endswith("download.php") and "P" in data:
                if data["P"] == "I":
                    self.do_wait()

                elif data["P"] == "IV":
                    break

            m = re.search(self.DATA_PATTERN, self.data)
            if m is None:
                self.error(self._("Data pattern not found"))

            url = "http://datei.to/" + m.group(1)
            data = dict(x.split("=") for x in m.group(2).split("&"))

            if url.endswith("self.captcha.php"):
                (
                    data["recaptcha_response_field"],
                    data["recaptcha_challenge_field"],
                ) = self.captcha.challenge()
        else:
            return

        self.link = self.data

    def do_wait(self):
        m = re.search(self.WAIT_PATTERN, self.data)
        wait_time = int(m.group(1)) if m else 30

        self.load("http://datei.to/ajax/download.php", post={"P": "Ads"})
        self.wait(wait_time, False)
