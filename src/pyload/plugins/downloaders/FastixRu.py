# -*- coding: utf-8 -*-

import json

from ..base.multi_downloader import MultiDownloader


class FastixRu(MultiDownloader):
    __name__ = "FastixRu"
    __type__ = "downloader"
    __version__ = "0.22"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?fastix\.(ru|it)/file/\w{24}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Fastix multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Massimo Rosamilia", "max@spiritix.eu")]

    def setup(self):
        self.chunk_limit = 3

    def handle_premium(self, pyfile):
        self.data = self.load(
            "http://fastix.ru/api_v2/",
            get={
                "apikey": self.account.get_data("apikey"),
                "sub": "getdirectlink",
                "link": pyfile.url,
            },
        )
        data = json.loads(self.data)

        self.log_debug("Json data", data)

        if 'error":true' in self.data:
            self.offline()
        else:
            self.link = data["downloadlink"]
