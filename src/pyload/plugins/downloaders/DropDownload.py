# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class DropDownload(XFSDownloader):
    __name__ = "DropDownload"
    __type__ = "downloader"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?drop\.download/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Drop.download downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "drop.download"
    LINK_PATTERN = r'<a href="(https://s\d+\.drop\.download.+?)"'

    DL_LIMIT_PATTERN = r"You have reached the download-limit: [\d.,]+\s*[a-zA-Z]* for last (\d+ days)"

    def setup(self):
        self.multi_dl = True
        self.resume_download = True
        self.chunk_limit = -1
