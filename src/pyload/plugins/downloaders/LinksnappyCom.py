# -*- coding: utf-8 -*-
import json
import re
import urllib.parse

from ..base.multi_downloader import MultiDownloader


class LinksnappyCom(MultiDownloader):
    __name__ = "LinksnappyCom"
    __type__ = "downloader"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r"https?://(?:[^/]+\.)?linksnappy\.com"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Linksnappy.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it"), ("Bilal Ghouri", None)]

    def handle_premium(self, pyfile):
        host = self._get_host(pyfile.url)
        json_params = json.dumps(
            {
                "link": pyfile.url,
                "type": host,
                "username": self.account.user,
                "password": self.account.get_login("password"),
            }
        )

        r = self.load(
            "https://linksnappy.com/api/linkgen", post={"genLinks": json_params}
        )

        self.log_debug("JSON data: " + r)

        j = json.loads(r)["links"][0]

        if j["error"]:
            self.error(self._("Error converting the link"))

        pyfile.name = j["filename"]
        self.link = j["generated"]

    @staticmethod
    def _get_host(url):
        host = urllib.parse.urlsplit(url).netloc
        return re.search(r"[\w\-]+\.\w+$", host).group(0)
