# -*- coding: utf-8 -*-

import hashlib
import json

import pycurl
from pyload.core.utils import seconds

from ..base.multi_downloader import MultiDownloader


class LinkifierCom(MultiDownloader):
    __name__ = "LinkifierCom"
    __type__ = "downloader"
    __version__ = "0.04"
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

    __description__ = """Linkifier.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_KEY = "d046c4309bb7cabd19f49118a2ab25e0"
    API_URL = "https://api.linkifier.com/downloadapi.svc/"

    def api_request(self, method, user, password, **kwargs):
        post = {
            "login": user,
            "md5Pass": hashlib.md5(password.encode()).hexdigest(),
            "apiKey": self.API_KEY,
        }
        post.update(kwargs)
        self.req.http.c.setopt(
            pycurl.HTTPHEADER, ["Content-Type: application/json; charset=utf-8"]
        )
        res = json.loads(self.load(self.API_URL + method, post=json.dumps(post)))
        self.req.http.c.setopt(
            pycurl.HTTPHEADER, ["Content-Type: text/html; charset=utf-8"]
        )
        return res

    def setup(self):
        self.multi_dl = True

    def handle_premium(self, pyfile):
        json_data = self.api_request(
            "stream",
            self.account.user,
            self.account.info["login"]["password"],
            url=pyfile.url,
        )

        if json_data["hasErrors"]:
            error_msg = json_data["ErrorMSG"] or "Unknown error"
            if error_msg in (
                "Customer reached daily limit for current hoster",
                "Accounts are maxed out for current hoster",
            ):
                self.retry(wait=seconds.to_midnight())

            self.fail(error_msg)

        self.resume_download = json_data["con_resume"]
        self.chunk_limit = json_data.get("con_max", 1) or 1
        self.url = json_data["url"]
