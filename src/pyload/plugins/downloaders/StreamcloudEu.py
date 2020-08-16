# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class StreamcloudEu(XFSDownloader):
    __name__ = "StreamcloudEu"
    __type__ = "downloader"
    __version__ = "0.16"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?streamcloud\.eu/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Streamcloud.eu downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("seoester", "seoester@googlemail.com")]

    PLUGIN_DOMAIN = "streamcloud.eu"

    WAIT_PATTERN = r"var count = (\d+)"

    def setup(self):
        self.multi_dl = True
        self.chunk_limit = 1
        self.resume_download = self.premium
