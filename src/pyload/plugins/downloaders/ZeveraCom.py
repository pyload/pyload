# -*- coding: utf-8 -*-

import json

from ..base.multi_downloader import MultiDownloader


class ZeveraCom(MultiDownloader):
    __name__ = "ZeveraCom"
    __type__ = "downloader"
    __version__ = "0.39"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)zevera\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Zevera.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://www.zevera.com/api/"

    def api_response(self, method, api_key, **kwargs):
        get_data = {"client_id": "452508742", "apikey": api_key}

        get_data.update(kwargs)

        res = self.load(self.API_URL + method, get=get_data)

        return json.loads(res)

    def handle_premium(self, pyfile):
        res = self.api_response(
            "transfer/directdl", self.account.info["login"]["password"], src=pyfile.url
        )
        if res["status"] == "success":
            self.link = res["location"]
            pyfile.name = res["filename"]
            pyfile.size = res["filesize"]

        else:
            self.fail(res["message"])
