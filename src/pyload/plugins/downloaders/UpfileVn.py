# -*- coding: utf-8 -*-

import hashlib
import json

from ..base.simple_downloader import SimpleDownloader


class UpfileVn(SimpleDownloader):
    __name__ = "UpfileVn"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?upfile\.vn/(?P<ID>.+?)/.+?\.html"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Upfile.Vn downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    INFO_PATTERN = r"<h1>(?P<N>.+?) \((?P<S>[\d.,]+)(?P<U>[\w^_]+)\)</h1>"

    WAIT_PATTERN = r"data-count=\'(\d+)\'"

    def handle_free(self, pyfile):
        id = self.info["pattern"]["ID"] + "7891"
        token = hashlib.sha256(id.encode()).hexdigest().upper()

        self.data = self.load(pyfile.url, post={"Token": token})

        json_data = json.loads(self.data)

        if json_data["Status"] is True:
            self.link = json_data["Link"]

        else:
            self.log_debug(f"Download failed: {json_data}")
