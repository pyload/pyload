# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.simple_downloader import SimpleDownloader


def decode_cloudflare_email(value):
    email = ""

    key = int(value[:2], 16)
    for i in range(2, len(value), 2):
        email += chr(int(value[i : i + 2], 16) ^ key)

    return email


class UpleaCom(SimpleDownloader):
    __name__ = "UpleaCom"
    __type__ = "downloader"
    __version__ = "0.21"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?uplea\.com/dl/\w{15}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Uplea.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Redleon", None), ("GammaC0de", None)]

    PLUGIN_DOMAIN = "uplea.com"

    SIZE_REPLACEMENTS = [
        ("ko", "KiB"),
        ("mo", "MiB"),
        ("go", "GiB"),
        ("Ko", "KiB"),
        ("Mo", "MiB"),
        ("Go", "GiB"),
    ]

    NAME_PATTERN = r'<span class="gold-text">(?P<N>.+?)</span>'
    SIZE_PATTERN = (
        r'<span class="label label-info agmd">(?P<S>[\d.,]+) (?P<U>[\w^_]+?)</span>'
    )
    OFFLINE_PATTERN = r">You followed an invalid or expired link"

    LINK_PATTERN = r'"(https?://\w+\.uplea\.com/anonym/.*?)"'

    PREMIUM_ONLY_PATTERN = (
        r"You need to have a Premium subscription to download this file"
    )
    WAIT_PATTERN = r"timeText: ?(\d+),"
    STEP_PATTERN = r'<a href="(/step/.+)">'

    NAME_REPLACEMENTS = [
        (
            r'(<a class="__cf_email__" .+? data-cfemail="(\w+?)".+)',
            lambda x: decode_cloudflare_email(x.group(2)),
        )
    ]

    def setup(self):
        self.multi_dl = False
        self.chunk_limit = 1
        self.resume_download = True

    def handle_free(self, pyfile):
        m = re.search(self.STEP_PATTERN, self.data)
        if m is None:
            self.error(self._("STEP_PATTERN not found"))

        self.data = self.load(urllib.parse.urljoin("http://uplea.com/", m.group(1)))

        m = re.search(self.WAIT_PATTERN, self.data)
        if m is not None:
            self.wait(m.group(1), True)
            self.retry()

        m = re.search(self.LINK_PATTERN, self.data)
        if m is None:
            self.error(self._("LINK_PATTERN not found"))

        self.link = m.group(1)

        m = re.search(r".ulCounter\({'timer':(\d+)}\)", self.data)
        if m is not None:
            self.wait(m.group(1))
