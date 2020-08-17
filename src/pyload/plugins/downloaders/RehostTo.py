# -*- coding: utf-8 -*-

from ..base.multi_downloader import MultiDownloader


class RehostTo(MultiDownloader):
    __name__ = "RehostTo"
    __type__ = "downloader"
    __version__ = "0.29"
    __status__ = "testing"

    __pattern__ = r"https?://.*rehost\.to\..+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Rehost.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net")]

    def handle_premium(self, pyfile):
        self.download(
            "http://rehost.to/process_download.php",
            get={
                "user": "cookie",
                "pass": self.account.get_data("session"),
                "dl": pyfile.url,
            },
            disposition=True,
        )
