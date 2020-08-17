# -*- coding: utf-8 -*-

import json

from pyload.core.utils import parse

from ..base.multi_downloader import MultiDownloader


class AlldebridCom(MultiDownloader):
    __name__ = "AlldebridCom"
    __type__ = "downloader"
    __version__ = "0.58"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.|s\d+\.)?alldebrid\.com/dl/[\w^_]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Alldebrid.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Andy Voigt", "spamsales@online.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://docs.alldebrid.com/
    API_URL = "https://api.alldebrid.com/"

    def api_response(self, method, **kwargs):
        kwargs["agent"] = "pyLoad"
        kwargs["version"] = self.pyload.version
        html = self.load(self.API_URL + method, get=kwargs)
        return json.loads(html)

    def setup(self):
        self.chunk_limit = 16

    def handle_premium(self, pyfile):
        json_data = self.api_response(
            "link/unlock", link=pyfile.url, token=self.account.info["data"]["token"]
        )

        if json_data.get("error", False):
            if json_data.get("errorCode", 0) in (12, 31):
                self.offline()

            else:
                self.log_warning(json_data["error"])
                self.temp_offline()

        else:
            pyfile.name = json_data["infos"]["filename"]
            pyfile.size = parse.bytesize(json_data["infos"]["filesize"])
            self.link = json_data["infos"]["link"]
