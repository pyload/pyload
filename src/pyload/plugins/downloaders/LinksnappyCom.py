# -*- coding: utf-8 -*-

import time
import json

from ..base.multi_downloader import MultiDownloader


class LinksnappyCom(MultiDownloader):
    __name__ = "LinksnappyCom"
    __type__ = "downloader"
    __version__ = "0.19"
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
    __authors__ = [("stickell", "l.stickell@yahoo.it"),
			       ("Bilal Ghouri", None),
			       ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://linksnappy.com/api/"

    def api_response(self, method, **kwargs):
        return json.loads(self.load(self.API_URL + method,
                                    get=kwargs))

    def handle_premium(self, pyfile):
        json_params = json.dumps({'link': pyfile.url})

        api_data = self.api_response("linkgen", genLinks=json_params)["links"][0]

        if api_data["status"] != "OK":
            self.fail(api_data["error"])

        if api_data.get("cacheDL", False):
            self._cache_dl(api_data["hash"])

        pyfile.name = api_data["filename"]
        self.link = api_data["generated"]

    def _cache_dl(self,file_hash):
        self.pyfile.set_custom_status("server dl")
        self.pyfile.set_progress(0)

        while True:
            api_data = self.api_response("CACHEDLSTATUS", id=file_hash)

            if api_data["status"] != "OK":
                self.fail(api_data["error"])

            progress = api_data["return"]["percent"]
            self.pyfile.setProgress(progress)
            if progress == 100:
                break

            self._sleep(2)

    def _sleep(self, sec):
        for _i in range(sec):
            if self.pyfile.abort:
                break
            time.sleep(1)
