# -*- coding: utf-8 -*-

from datetime import timedelta

from ..base.multi_downloader import MultiDownloader


class PremiumTo(MultiDownloader):
    __name__ = "PremiumTo"
    __type__ = "downloader"
    __version__ = "0.33"
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

    def handle_premium(self, pyfile):
        self.download(
            "http://api.premium.to/api/getfile.php",
            get={
                "username": self.account.user,
                "password": self.account.info["login"]["password"],
                "link": pyfile.url,
            },
            disposition=True,
        )

    def check_download(self):
        if self.scan_download({"nopremium": "No premium account available"}):
            self.retry(60, timedelta(minutes=5).seconds, "No premium account available")

        err = ""
        if self.req.http.code == 420:
            #: Custom error code sent - fail
            file = encode(self.last_download)

            with open(file, mode="rb") as fp:
                err = fp.read(256).strip()

            self.remove(file)

        if err:
            self.fail(err)

        return MultiDownloader.check_download(self)
