# -*- coding: utf-8 -*-

import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_downloader import MultiDownloader


def args(**kwargs):
    return kwargs


class RealdebridCom(MultiDownloader):
    __name__ = "RealdebridCom"
    __type__ = "downloader"
    __version__ = "0.81"
    __status__ = "testing"

    __pattern__ = r"https?://((?:www\.|s\d+\.)?real-debrid\.com/dl?/|[\w^_]\.rdb\.so/d/)[\w^_]+"
    __config__ = [
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Real-Debrid.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Devirex Hazzard", "naibaf_11@yahoo.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://api.real-debrid.com/
    API_URL = "https://api.real-debrid.com/rest/1.0"

    def api_request(self, namespace, get={}, post={}):
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))
        try:
            json_data = self.load(self.API_URL + namespace, get=get, post=post)

        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def setup(self):
        self.chunk_limit = 3

    def handle_premium(self, pyfile):
        user = list(self.account.accounts.keys())[0]
        api_token = self.account.accounts[user]["api_token"]

        data = self.api_request(
            "/unrestrict/link",
            args(auth_token=api_token),
            args(link=pyfile.url, password=self.get_password()),
        )

        self.log_debug(f"Returned Data: {data}")

        if "error" in data:
            if data['error_code'] == 24:
                self.offline()

            elif data['error_code'] == 8:  #: Token expired?
                self.account.relogin()
                self.retry()

            else:
                self.fail("{} (code: {})".format(data["error"], data["error_code"]))

        else:
            if data["filename"]:
                pyfile.name = data["filename"]

            pyfile.size = data["filesize"]
            self.link = data["download"]
