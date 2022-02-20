# -*- coding: utf-8 -*-

from datetime import timedelta

from ..base.multi_downloader import MultiDownloader
from ..helpers import replace_patterns


class SimplydebridCom(MultiDownloader):
    __name__ = "SimplydebridCom"
    __type__ = "downloader"
    __version__ = "0.27"
    __status__ = "testing"

    __pattern__ = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/sd\.php"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Simply-debrid.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Kagenoshin", "kagenoshin@gmx.ch")]

    def handle_premium(self, pyfile):
        #: Fix the links for simply-debrid.com!
        rules = [
            ("clz.to", "cloudzer.net/file"),
            ("http://share-online", "http://www.share-online"),
            ("ul.to", "uploaded.net/file"),
            ("uploaded.com", "uploaded.net"),
            ("filerio.com", "filerio.in"),
            ("lumfile.com", "lumfile.se"),
        ]
        self.link = replace_patterns(pyfile.url, rules)

        if "fileparadox" in self.link:
            self.link = self.link.replace("http://", "https://")

        self.data = self.load("http://simply-debrid.com/api.php", get={"dl": self.link})
        if (
            "tiger Link" in self.data
            or "Invalid Link" in self.data
            or ("API" in self.data and "ERROR" in self.data)
        ):
            self.error(self._("Unable to unrestrict link"))

        self.link = self.data

        self.wait(5)

    def check_download(self):
        if self.scan_download({"error": b"No address associated with hostname"}):
            self.retry(24, timedelta(minutes=3).total_seconds(), self._("Bad file downloaded"))

        return MultiDownloader.check_download(self)
