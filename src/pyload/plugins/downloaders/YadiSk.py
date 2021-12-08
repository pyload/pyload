# -*- coding: utf-8 -*-

import json
import random
import re

from ..base.simple_downloader import SimpleDownloader


class YadiSk(SimpleDownloader):
    __name__ = "YadiSk"
    __type__ = "downloader"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r"https?://yadi\.sk/d/[\w\-]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Yadi.sk downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", None)]

    OFFLINE_PATTERN = r"Nothing found"

    def get_info(self, url="", html=""):
        info = super(SimpleDownloader, self).get_info(url, html)

        if html:
            if "idclient" not in info:
                info["idclient"] = ""
                for _ in range(32):
                    info["idclient"] += random.choice("0123456abcdef")

            m = re.search(
                r'<script id="models-client" type="application/json">(.+?)</script>',
                html,
            )
            if m is not None:
                api_data = json.loads(m.group(1))
                try:
                    for sect in api_data:
                        if "model" in sect:
                            if sect["model"] == "config":
                                info["version"] = sect["data"]["version"]
                                info["sk"] = sect["data"]["sk"]

                            elif sect["model"] == "resource":
                                info["id"] = sect["data"]["id"]
                                info["size"] = sect["data"]["meta"]["size"]
                                info["name"] = sect["data"]["name"]

                except Exception as exc:
                    info["status"] = 8
                    info["error"] = "Unexpected server response: {}".format(exc)

            else:
                info["status"] = 8
                info["error"] = "could not find required json data"

        return info

    def setup(self):
        self.resume_download = False
        self.multi_dl = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        if any(True for k in ["id", "sk", "version", "idclient"] if k not in self.info):
            self.error(self._("Missing JSON data"))

        try:
            self.data = self.load(
                "https://yadi.sk/models/",
                get={"_m": "do-get-resource-url"},
                post={
                    "idClient": self.info["idclient"],
                    "version": self.info["version"],
                    "_model.0": "do-get-resource-url",
                    "sk": self.info["sk"],
                    "id.0": self.info["id"],
                },
            )

            self.link = json.loads(self.data)["models"][0]["data"]["file"]

        except Exception:
            pass
