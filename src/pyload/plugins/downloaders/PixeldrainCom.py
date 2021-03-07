# -*- coding: utf-8 -*-

import json
import re

from pyload.core.network.request_factory import get_url

from ..base.simple_downloader import SimpleDownloader


class PixeldrainCom(SimpleDownloader):
    __name__ = "PixeldrainCom"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?pixeldrain\.com/u/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Pixeldrain.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    DIRECT_LINK = False

    API_URL = "https://pixeldrain.com/api/"
    #: See https://pixeldrain.com/api/

    @classmethod
    def api_info(cls, url):
        file_id = re.match(cls.__pattern__, url).group("ID")
        json_data = get_url(f"{cls.API_URL}/file/{file_id}/info")
        file_info = json.loads(json_data)

        if file_info["success"] is False:
            return {"status": 1}

        else:
            return {"name": file_info["name"], "size": file_info["size"], "status": 2}

    def handle_free(self, pyfile):
        file_id = self.info["pattern"]["ID"]
        self.download(f"{self.API_URL}/file/{file_id}")
