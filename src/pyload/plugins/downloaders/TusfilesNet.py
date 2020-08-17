# -*- coding: utf-8 -*-

from pyload.core.network.exceptions import Retry
from pyload.core.network.http.exceptions import BadHeader

from ..base.xfs_downloader import XFSDownloader


class TusfilesNet(XFSDownloader):
    __name__ = "TusfilesNet"
    __type__ = "downloader"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?tusfiles\.net/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Tusfiles.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("guidobelix", "guidobelix@hotmail.it"),
    ]

    PLUGIN_DOMAIN = "tusfiles.net"

    INFO_PATTERN = r"\](?P<N>.+) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)\["

    def setup(self):
        self.chunk_limit = -1
        self.multi_dl = True
        self.limit_dl = 2
        self.resume_download = True

    def download(self, url, *args, **kwargs):
        try:
            return super().download(url, *args, **kwargs)

        except BadHeader as exc:
            if exc.code == 503:
                self.multi_dl = False
                raise Retry("503")
