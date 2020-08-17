# -*- coding: utf-8 -*-
import json
import re

from pyload.core.utils import seconds

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class DatafileCom(SimpleDownloader):
    __name__ = "DatafileCom"
    __type__ = "downloader"
    __version__ = "0.05"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?datafile\.com/d/(?P<ID>\w{17})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Datafile.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<div class="file-name">(?P<N>.+?)</div>'
    SIZE_PATTERN = r'>Filesize: <span class="lime">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r"Invalid Link|Link Expired|This file was deleted"
    TEMP_OFFLINE_PATTERN = r"You are downloading another file at this moment"
    PREMIUM_ONLY_PATTERN = r"This file is only available for premium users"

    DIRECT_LINK = False
    DISPOSITION = False

    def handle_free(self, pyfile):
        m = re.search(r'<span class="time">([\d:]+)<', self.data)
        if m is not None:
            wait_time = sum(
                int(d) * 60 ** i for i, d in enumerate(reversed(m.group(1).split(":")))
            )

        else:
            wait_time = 0

        self.captcha = ReCaptcha(pyfile)
        captcha_key = self.captcha.detect_key()

        if captcha_key:
            response, challenge = self.captcha.challenge(captcha_key)

            post_data = {
                "doaction": "validateCaptcha",
                "recaptcha_challenge_field": challenge,
                "recaptcha_response_field": response,
                "fileid": self.info["pattern"]["ID"],
            }

            catcha_result = json.loads(
                self.load("http://www.datafile.com/files/ajax.html", post=post_data)
            )

            if not catcha_result["success"]:
                self.retry_captcha()

            self.captcha.correct()

            self.wait(wait_time)

            post_data["doaction"] = "getFileDownloadLink"
            post_data["token"] = catcha_result["token"]

            file_info = json.loads(
                self.load("http://www.datafile.com/files/ajax.html", post=post_data)
            )
            if file_info["success"]:
                self.link = file_info["link"]
                self.log_debug(f"URL:{self.link}")

        else:
            m = re.search(r"error\.html\?code=(\d+)", self.req.last_effective_url)
            if m is not None:
                error_code = int(m.group(1))
                if error_code in (2, 3):
                    self.offline()

                elif error_code == 7:
                    wait_time = seconds.to_midnight()
                    self.retry(wait=wait_time, msg=self._("Download limit exceeded"))

                elif error_code == 9:
                    self.temp_offline()

                else:
                    self.log_debug(f"Unknown error code {error_code}")
