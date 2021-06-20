# -*- coding: utf-8 -*-
import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_downloader import MultiDownloader


def args(**kwargs):
    return kwargs


class MegaDebridEu(MultiDownloader):
    __name__ = "MegaDebridEu"
    __type__ = "downloader"
    __version__ = "0.60"
    __status__ = "testing"

    __pattern__ = r"http://((?:www\d+\.|s\d+\.)?mega-debrid\.eu|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/download/file/[\w^_]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Mega-debrid.eu multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Devirex Hazzard", "naibaf_11@yahoo.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
        ("FoxyDarnec", "goupildavid[AT]gmail[DOT]com"),
    ]

    API_URL = "https://www.mega-debrid.eu/api.php"

    def api_request(self, action, get={}, post={}):
        get["action"] = action

        # Better use pyLoad User-Agent so we don't get blocked
        self.req.http.c.setopt(
            pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version).encode()
        )

        json_data = self.load(self.API_URL, get=get, post=post)

        return json.loads(json_data)

    def handle_premium(self, pyfile):
        try:
            res = self.api_request(
                "getLink",
                get=args(
                    token=self.account.info["data"]["cache_info"][self.account.user][
                        "token"
                    ]
                ),
                post=args(link=pyfile.url),
            )

        except BadHeader as exc:
            if exc.code == 405:
                self.fail(self._("Banned IP"))

            else:
                raise

        if res["response_code"] == "ok":
            self.link = res["debridLink"]

        elif res["response_code"] == "TOKEN_ERROR":
            self.account.relogin()
            self.retry()

        elif res["response_code"] == "UNALLOWED_IP":
            self.fail(self._("Banned IP"))

        else:
            self.log_error(res["response_text"])
            self.fail(res["response_text"])
