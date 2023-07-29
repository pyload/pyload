# -*- coding: utf-8 -*-

import json

from ..base.simple_downloader import SimpleDownloader


class WorkuploadCom(SimpleDownloader):
    __name__ = "WorkuploadCom"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://workupload\.com/(?:file|start)/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Workupload.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://workupload.com/api/"

    INFO_PATTERN = r"<td>Filename:\xa0</td><td [^>]+>(?P<N>.+?)</td></tr><tr><td>Filesize:\xa0</td><td>(?P<S>\d+) \((?P<U>[\w^_]+)\)</td></tr><tr><td>Checksum:\xa0</td><td [^>]+>(?P<D>\w+) \((?P<H>\w+)\)<"
    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://workupload.com/file/\g<ID>")]

    def api_request(self, method, **kwargs):
        json_data = self.load(self.API_URL + method)
        return json.loads(json_data)

    def setup(self):
        self.multi_dl = True

    def handle_free(self, pyfile):
        api_data = self.api_request("file/getDownloadServer/" + self.info["pattern"]["ID"])
        if api_data["success"]:
            self.link = api_data["data"]["url"]
