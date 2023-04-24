# -*- coding: utf-8 -*-

import json
import re

import pycurl

from ..base.simple_downloader import SimpleDownloader


class KrakenfilesCom(SimpleDownloader):
    __name__ = "KrakenfilesCom"
    __type__ = "downloader"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?krakenfiles\.com/view/\w+/file.html"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Krakenfiles.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'class="coin-name"><h5>(?P<N>.+?)<'
    SIZE_PATTERN = r"File size</div>\s.+?>(?P<S>[\d.,]+) (?P<U>[\w^_]+)<"

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('id="dl-form"')
        if url is None:
            self.fail(_("Free download form not found"))

        m = re.search(r'<div.+?data-file-hash="(\w+?)".*?>', self.data)
        if m is None:
            self.fail(_("hash pattern not found"))

        self.req.http.c.setopt(
            pycurl.HTTPHEADER,
            ["X-Requested-With: XMLHttpRequest", f"hash: {m.group(1)}"],
        )
        self.data = self.load(self.fixurl(url), post=inputs)
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        json_data = json.loads(self.data)
        if json_data.get("status") == "ok":
            self.download(json_data["url"], ref="https://krakenfiles.com/")
