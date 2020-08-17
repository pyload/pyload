# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.simple_downloader import SimpleDownloader


class FileboomMe(SimpleDownloader):
    __name__ = "FileboomMe"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"https?://f(?:ile)?boom\.me/file/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Fileboom.me downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", None)]

    NAME_PATTERN = r'<i class="icon-download"></i>\s*(?P<N>.+?)\s*<'
    SIZE_PATTERN = r"File size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)"
    OFFLINE_PATTERN = r">This file is no longer available"

    WAIT_PATTERN = r'<div class="tik-tak">([\d:]+)'
    LINK_PATTERN = r"/file/url\.html\?file=\w+"

    CAPTCHA_PATTERN = r'<img .* src="(/file/captcha.html\?v=\w+)"'

    def setup(self):
        self.resume_download = True
        self.multi_dl = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        post_url = urllib.parse.urljoin(
            pyfile.url, "/file/" + self.info["pattern"]["ID"]
        )

        m = re.search(r'data-slow-id="(\w+)"', self.data)
        if m is not None:
            self.data = self.load(post_url, post={"slow_id": m.group(1)})

            m = re.search(self.LINK_PATTERN, self.data)
            if m is not None:
                self.link = urllib.parse.urljoin(pyfile.url, m.group(0))

            else:
                m = re.search(
                    r'<input type="hidden" name="uniqueId" value="(\w+)">', self.data
                )
                if m is None:
                    m = re.search(r">\s*Please wait ([\d:]+)", self.data)
                    if m is not None:
                        wait_time = 0
                        for v in re.findall(r"(\d+)", m.group(1), re.I):
                            wait_time = 60 * wait_time + int(v)
                        self.wait(wait_time)
                        self.retry()

                else:
                    uniqueId = m.group(1)

                    m = re.search(self.CAPTCHA_PATTERN, self.data)
                    if m is not None:
                        captcha = self.captcha.decrypt(
                            urllib.parse.urljoin(pyfile.url, m.group(1))
                        )
                        self.data = self.load(
                            post_url,
                            post={
                                "CaptchaForm[verifyCode]": captcha,
                                "free": 1,
                                "freeDownloadRequest": 1,
                                "uniqueId": uniqueId,
                            },
                        )

                        if "The verification code is incorrect" in self.data:
                            self.retry_captcha()

                        else:
                            self.check_errors()

                            self.data = self.load(
                                post_url, post={"free": 1, "uniqueId": uniqueId}
                            )

                            m = re.search(self.LINK_PATTERN, self.data)
                            if m is not None:
                                self.link = urllib.parse.urljoin(pyfile.url, m.group(0))
