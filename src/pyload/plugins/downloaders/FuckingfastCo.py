# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class FuckingfastCo(SimpleDownloader):
    __name__ = "FuckingfastCo"
    __version__ = "0.01"
    __type__ = "downloader"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?fuckingfast\.co/[A-Za-z0-9]+(?:#.*)?'
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """FuckingFast.co downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Alexander Sulfrian", "alexander@sulfrian.net"),
    ]

    LINK_PATTERN = (
        r'window\.open\(["\'](https://fuckingfast\.co/dl/[^"\']+)["\']'
    )
    NAME_PATTERN = r'<title>(?P<N>.+?)<'
    SIZE_PATTERN = r'<span class="text-gray-500">Size: (?P<S>[\d.,]*)(?P<U>[\w^_]*) \|'

    def setup(self):
        self.resume_download = True
        self.multi_dl = True
