# -*- coding: utf-8 -*-

import re
import urllib.parse
from datetime import timedelta

from ..base.simple_downloader import SimpleDownloader


class UnibytesCom(SimpleDownloader):
    __name__ = "UnibytesCom"
    __type__ = "downloader"
    __version__ = "0.21"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?unibytes\.com/[\w\- .]{11}B"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """UniBytes.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    PLUGIN_DOMAIN = "unibytes.com"

    INFO_PATTERN = r'<span[^>]*?id="fileName".*?>(?P<N>.+?)</span>\s*\((?P<S>\d.*?)\)'

    WAIT_PATTERN = r'Wait for <span id="slowRest">(\d+)</span> sec'
    LINK_FREE_PATTERN = r'<a href="(.+?)">Download</a>'

    def handle_free(self, pyfile):
        domain = "http://www.{}/".format(self.PLUGIN_DOMAIN)
        action, post_data = self.parse_html_form('id="startForm"')

        for _ in range(3):
            self.log_debug(action, post_data)
            self.data = self.load(
                urllib.parse.urljoin(domain, action), post=post_data, redirect=False
            )

            location = self.last_header.get("location")
            if location:
                self.link = location
                return

            if (
                ">Somebody else is already downloading using your IP-address<"
                in self.data
            ):
                self.wait(timedelta(minutes=10).total_seconds(), True)
                self.restart()

            if post_data["step"] == "last":
                m = re.search(self.LINK_FREE_PATTERN, self.data)
                if m is not None:
                    self.captcha.correct()
                    self.link = m.group(1)
                    break
                else:
                    self.retry_captcha()

            last_step = post_data["step"]
            action, post_data = self.parse_html_form('id="stepForm"')

            if last_step == "timer":
                m = re.search(self.WAIT_PATTERN, self.data)
                self.wait(m.group(1) if m else 60, False)

            elif last_step in ("captcha", "last"):
                post_data["captcha"] = self.captcha.decrypt(
                    urllib.parse.urljoin(domain, "captcha.jpg")
                )
