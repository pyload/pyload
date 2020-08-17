# -*- coding: utf-8 -*-

import random

from ..base.simple_downloader import SimpleDownloader


class GigapetaCom(SimpleDownloader):
    __name__ = "GigapetaCom"
    __type__ = "downloader"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?gigapeta\.com/dl/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """GigaPeta.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<img src=".*" alt="file" />-->\s*(?P<N>.*?)\s*</td>'
    SIZE_PATTERN = r"<th>\s*Size\s*</th>\s*<td>\s*(?P<S>.*?)\s*</td>"
    OFFLINE_PATTERN = r'<div id="page_error">'

    DOWNLOAD_PATTERN = r'"All threads for IP'

    COOKIES = [("gigapeta.com", "lang", "us")]

    def handle_free(self, pyfile):
        captcha_key = str(random.randint(1, 100_000_000))
        captcha_url = "http://gigapeta.com/img/captcha.gif?x={}".format(captcha_key)

        self.check_errors()

        captcha = self.captcha.decrypt(captcha_url)
        header = self.load(
            pyfile.url,
            post={
                "captcha_key": captcha_key,
                "captcha": captcha,
                "download": "Download",
            },
            just_header=True,
        )

        self.link = header.get("location")
