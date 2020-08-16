# -*- coding: utf-8 -*-

import os
import re
import time

from pyload.core.network.request_factory import get_url

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class UploadedTo(SimpleDownloader):
    __name__ = "UploadedTo"
    __type__ = "downloader"
    __version__ = "1.08"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(uploaded\.(to|net)|ul\.to)(/file/|/?\?id=|.*?&id=|/)(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Uploaded.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    CHECK_TRAFFIC = True

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"http://uploaded.net/file/\g<ID>")]

    API_KEY = "lhF2IeeprweDfu9ccWlxXVVypA5nA3EL"

    OFFLINE_PATTERN = r">Page not found"
    TEMP_OFFLINE_PATTERN = (
        r"<title>uploaded\.net - Maintenance|Downloads have been blocked for today.<"
    )
    PREMIUM_ONLY_PATTERN = (
        r"This file exceeds the max\. filesize which can be downloaded by free users"
    )

    LINK_FREE_PATTERN = r"url:\s*'(.+?)'"
    LINK_PREMIUM_PATTERN = r'<div class="tfree".*\s*<form method="post" action="(.+?)"'

    WAIT_PATTERN = r"Current waiting period: <span>(\d+)"
    DL_LIMIT_PATTERN = (
        r"You have reached the max. number of possible free downloads for this hour"
    )

    @classmethod
    def api_info(cls, url):
        info = {}

        for _ in range(5):
            html = get_url(
                "http://uploaded.net/api/filemultiple",
                get={
                    "apikey": cls.API_KEY,
                    "id_0": re.match(cls.__pattern__, url).group("ID"),
                },
            )

            if html != "can't find request":
                api = html.split(",", 4)
                if api[0] == "online":
                    info.update(
                        {
                            "name": api[4].strip(),
                            "size": api[2],
                            "status": 2,
                            "sha1": api[3],
                        }
                    )
                else:
                    info["status"] = 1
                break
            else:
                time.sleep(3)

        return info

    def setup(self):
        self.multi_dl = self.resume_download = self.premium
        self.chunk_limit = 1  #: Critical problems with more chunks

    def handle_free(self, pyfile):
        self.load("http://uploaded.net/language/en", just_header=True)

        self.data = self.load("http://uploaded.net/js/download.js")

        self.captcha = ReCaptcha(pyfile)
        response, challenge = self.captcha.challenge()

        self.data = self.load(
            "http://uploaded.net/io/ticket/captcha/{}".format(
                self.info["pattern"]["ID"]
            ),
            post={"g-recaptcha-response": response},
        )
        self.check_errors()

        super().handle_free(pyfile)
        self.check_errors()

    def check_download(self):
        check = self.scan_download({"dl_limit": self.DL_LIMIT_PATTERN})

        if check == "dl_limit":
            self.log_warning(self._("Free download limit reached"))
            os.remove(self.last_download)
            self.retry(wait=10800, msg=self._("Free download limit reached"))

        return super().check_download()
