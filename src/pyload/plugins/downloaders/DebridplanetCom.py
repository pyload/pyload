# -*- coding: utf-8 -*-

import json

import pycurl

from ..base.multi_downloader import MultiDownloader


class DebridplanetCom(MultiDownloader):
    __name__ = "DebridplanetCom"
    __type__ = "downloader"
    __version__ = "0.01"
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

    __description__ = """Debridplanet.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://debridplanet.com/v1/"

    def api_request(self, method, **kwargs):
        token = self.account.info["data"].get("token")
        if token is not None:
            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Authorization: Bearer " + token]
            )
        json_data = self.load(f"{self.API_URL}{method}.php", post=json.dumps(kwargs))
        return json.loads(json_data)

    def handle_premium(self, pyfile):
        if self.account.relogin():  #: Insure valid API token
            api_data = self.api_request("gen_link", listurl=[pyfile.url])
            if len(api_data) > 0:
                if api_data[0]["success"]:
                    file_info = api_data[0]["data"]
                    pyfile.name = file_info["filename"]
                    pyfile.size = file_info["filesize"]
                    self.resume_download = file_info["resumable"]
                    self.link = file_info["link"]

                else:
                    err_msg = api_data[0]["message"]
                    self.log_error(err_msg)
                    self.fail(err_msg)
