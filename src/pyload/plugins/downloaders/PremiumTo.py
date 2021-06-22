# -*- coding: utf-8 -*-

import json
import re

from ..base.multi_downloader import MultiDownloader


class PremiumTo(MultiDownloader):
    __name__ = "PremiumTo"
    __type__ = "downloader"
    __version__ = "0.36"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Premium.to multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.net"),
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    CHECK_TRAFFIC = True

    # See https://premium.to/API.html
    API_URL = "http://api.premium.to/api/2/"

    def handle_premium(self, pyfile):
        self.download(
            self.API_URL + "getfile.php",
            get={
                "userid": self.account.user,
                "apikey": self.account.info["login"]["password"],
                "link": pyfile.url,
            },
            disposition=True,
        )

    def check_download(self):
        if self.scan_download(
            {
                "json": re.compile(
                    rb'\A{["\']code["\']:\d+,["\']message["\']:(["\']).+?\1}\Z'
                )
            }
        ):
            with open(self.last_download, "r") as fp:
                json_data = json.loads(fp.read())

            self.remove(self.last_download)
            self.fail(
                self._("API error {} - {}").format(json_data["code"], json_data["message"])
            )

        return super().check_download()
