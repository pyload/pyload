# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class ExtmatrixCom(SimpleDownloader):
    __name__ = "ExtmatrixCom"
    __type__ = "downloader"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://www\.extmatrix\.com/(?:get|files)/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Extmatrix.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_PREMIUM = True
    INFO_PATTERN = r">Download \| (?P<N>.+?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)<"

    LINK_PATTERN = r'<a href="(https://s\w+\.extmatrix\.com/get/.+?)"'

    def setup(self):
        self.chunk_limit = -1

    def handle_premium(self, pyfile):
        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
