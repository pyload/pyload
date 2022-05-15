# -*- coding: utf-8 -*-

import json

import pycurl

from ..base.multi_downloader import MultiDownloader


class GetTwentyFourOrg(MultiDownloader):
    __name__ = "GetTwentyFourOrg"
    __type__ = "downloader"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", False),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = "GeT24.org multi-downloader plugin"
    __license__ = "GPLv3"
    __authors__ = ["get24", "contact@get24.org"]

    API_URL = "https://get24.org/api/"

    def api_request(self, method, **kwargs):
        self.req.http.c.setopt(
            pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version).encode()
        )
        json_data = self.load(self.API_URL + method, post=kwargs)
        return json.loads(json_data)

    def handle_premium(self, pyfile):
        rc = self.api_request(
            "debrid/geturl",
            email=self.account.user,
            passwd_sha256=self.account.info["data"]["passwd_sha256"],
            link=pyfile.url,
        )
        if rc.get("ok") is True:
            pyfile.name = rc["filename"]
            pyfile.size = rc["filesize"]  # bytes is not good here?
            self.link = rc["url"]

        elif rc.get("reason") in ("wrong url", "file removed"):
            self.offline()

        elif rc.get("reason") in (
            "host daily limit exceeded",
            "host disabled",
            "temporary error",
            "unknown error",
        ):
            self.log_warning(rc["reason"])
            self.temp_offline()

        else:
            self.fail(rc.get("reason", "unknown error"))
