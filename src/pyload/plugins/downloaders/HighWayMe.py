# -*- coding: utf-8 -*-

import re

from pyload.core.utils import seconds

from ..base.multi_downloader import MultiDownloader


class HighWayMe(MultiDownloader):
    __name__ = "HighWayMe"
    __type__ = "downloader"
    __version__ = "0.24"
    __status__ = "testing"

    __pattern__ = r"https?://.+high-way\.my"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """High-Way.me multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("EvolutionClip", "evolutionclip@live.de")]

    def setup(self):
        self.chunk_limit = 4

    def check_errors(self):
        if "<code>5</code>" in self.data:
            self.account.relogin()
            self.retry()

        elif "<code>9</code>" in self.data:
            self.offline()

        elif "downloadlimit" in self.data:
            self.log_warning(self._("Reached maximum connctions"))
            self.retry(5, 60, self._("Reached maximum connctions"))

        elif "trafficlimit" in self.data:
            self.log_warning(self._("Reached daily limit"))
            self.retry(
                wait=seconds.to_midnight(), msg="Daily limit for this host reached"
            )

        elif "<code>8</code>" in self.data:
            self.log_warning(
                self._("Hoster temporarily unavailable, waiting 1 minute and retry")
            )
            self.retry(5, 60, self._("Hoster is temporarily unavailable"))

    def handle_premium(self, pyfile):
        for _ in range(5):
            self.data = self.load(
                "https://high-way.me/load.php", get={"link": self.pyfile.url}
            )

            if self.data:
                self.log_debug("JSON data: " + self.data)
                break
        else:
            self.log_info(self._("Unable to get API data, waiting 1 minute and retry"))
            self.retry(5, 60, self._("Unable to get API data"))

        self.check_errors()

        try:
            self.pyfile.name = re.search(r"<name>(.+?)</name>", self.data).group(1)

        except AttributeError:
            self.pyfile.name = ""

        try:
            self.pyfile.size = re.search(r"<size>(\d+)</size>", self.data).group(1)

        except AttributeError:
            self.pyfile.size = 0

        self.link = re.search(r"<download>(.+?)</download>", self.data).group(1)
