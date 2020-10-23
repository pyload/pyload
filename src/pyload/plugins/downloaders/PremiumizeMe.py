# -*- coding: utf-8 -*-
import json

from ..base.multi_downloader import MultiDownloader


class PremiumizeMe(MultiDownloader):
    __name__ = "PremiumizeMe"
    __type__ = "downloader"
    __version__ = "0.33"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Premiumize.me multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Florian Franzen", "FlorianFranzen@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://www.premiumize.me/api
    API_URL = "https://www.premiumize.me/api/"

    def api_respond(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)

        return json.loads(json_data)

    def handle_premium(self, pyfile):
        res = self.api_respond("transfer/directdl",
                               src=pyfile.url,
                               apikey=self.account.info["login"]["password"])

        if res["status"] == "success":
            self.pyfile.name = res["content"][0]["path"]
            self.pyfile.size = res["content"][0]["size"]
            self.download(res["content"][0]["link"])

        else:
            self.fail(res["message"])
