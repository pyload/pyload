# -*- coding: utf-8 -*-

from ..accounts.DownsterNet import DownsterApi
from ..base.multi_downloader import MultiDownloader


class DownsterNet(MultiDownloader):
    __name__ = "DownsterNet"
    __type__ = "downloader"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", False),
    ]

    __description__ = """Downster.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    def setup(self):
        self.api = DownsterApi(self)

    def handle_free(self, pyfile):
        api_data = self.api.request("download/get", get={"url": pyfile.url})

        if not api_data["success"]:
            if "offline" in api_data["error"]:
                self.offline()

            else:
                self.fail(api_data["error"])

        pyfile.name = api_data["data"]["name"]
        pyfile.size = int(api_data["data"]["size"])

        self.link = api_data["data"]["downloadUrl"]
