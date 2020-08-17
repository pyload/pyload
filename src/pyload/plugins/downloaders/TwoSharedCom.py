# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class TwoSharedCom(SimpleDownloader):
    __name__ = "TwoSharedCom"
    __type__ = "downloader"
    __version__ = "0.19"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?2shared\.com/(account/)?(download|get|file|document|photo|video|audio)/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """2Shared.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r"<h1>(?P<N>.*)</h1>"
    SIZE_PATTERN = (
        r'<span class="dtitle">File size:</span>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    )
    OFFLINE_PATTERN = (
        r"The file link that you requested is not valid\.|This file was deleted\."
    )

    LINK_FREE_PATTERN = r"window.location =\'(.+?)\';"

    def setup(self):
        self.resume_download = True
        self.multi_dl = True
