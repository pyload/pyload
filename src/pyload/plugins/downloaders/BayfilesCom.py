# -*- coding: utf-8 -*-

import json
import re

from ..base.simple_downloader import SimpleDownloader


class BayfilesCom(SimpleDownloader):
    __name__ = "BayfilesCom"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https://bayfiles.com/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Bayfiles.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [(r"^http://", "https://")]

    LINK_PATTERN = r'href="(https://cdn-\d+\.bayfiles\.com/.+?)"'

    def api_info(self, url):
        info = {}
        file_id = re.match(self.__pattern__, url).group("ID")
        json_data = self.load(f"https://api.bayfiles.com/v2/file/{file_id}/info")
        api_data = json.loads(json_data)

        if api_data["status"] is True:
            info["status"] = 2
            info["name"] = api_data["data"]["file"]["metadata"]["name"]
            info["size"] = api_data["data"]["file"]["metadata"]["size"]["bytes"]

        else:
            if api_data["error"]["type"] in ("FILE_NOT_FOUND", "ERROR_FILE_BANNED"):
                info["status"] = 1

            else:
                info["error"] = api_data["error"]["message"]
                info["status"] = 8

        return info
