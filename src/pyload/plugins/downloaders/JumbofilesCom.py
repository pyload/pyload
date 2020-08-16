# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class JumbofilesCom(SimpleDownloader):
    __name__ = "JumbofilesCom"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?jumbofiles\.com/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """JumboFiles.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]

    INFO_PATTERN = r"<TR><TD>(?P<N>.+?)\s*<small>\((?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)"
    OFFLINE_PATTERN = r"Not Found or Deleted / Disabled due to inactivity or DMCA"
    LINK_FREE_PATTERN = r'<meta http-equiv="refresh" content="10;url=(.+)">'

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def handle_free(self, pyfile):
        post_data = {"id": self.info["pattern"]["ID"], "op": "download3", "rand": ""}
        html = self.load(self.pyfile.url, post=post_data)
        self.link = re.search(self.LINK_FREE_PATTERN, html).group(1)
