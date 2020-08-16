# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class DailyuploadsNet(SimpleDownloader):
    __name__ = "DailyuploadsNet"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?dailyuploads\.net/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Sendit.cloud downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r"<b>Filename:</b></td><td nowrap>(?P<N>.+?)</td>"
    SIZE_PATTERN = (
        r"<b>Size:</b></td><td>.+?<small>\((?P<S>[\d.,]+) (?P<U>bytes)\)</small>"
    )

    OFFLINE_PATTERN = r">File Not Found</"

    LINK_FREE_PATTERN = r'<a href="(https?://down\d+.dailyuploads.net(?::\d+)?/.+?)">'

    def setup(self):
        self.multi_dl = True
        self.resume_download = True
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('name="F1"')
        if inputs is not None:
            inputs["referer"] = pyfile.url
            self.data = self.load(pyfile.url, post=inputs)

            m = re.search(self.LINK_FREE_PATTERN, self.data)
            if m is not None:
                self.link = m.group(1)
