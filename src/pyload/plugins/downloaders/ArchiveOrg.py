# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class ArchiveOrg(SimpleDownloader):
    __name__ = "ArchiveOrg"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?archive\.org/download/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Archive.org downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def setup(self):
        self.multi_dl = True
        self.resume_download = True
        self.chunk_limit = -1
