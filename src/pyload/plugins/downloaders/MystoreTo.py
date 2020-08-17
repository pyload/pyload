# -*- coding: utf-8 -*-
import re

from ..base.simple_downloader import SimpleDownloader

#
# Test link:
#   http://mystore.to/dl/mxcA50jKfP


class MystoreTo(SimpleDownloader):
    __name__ = "MystoreTo"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?mystore\.to/dl/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Mystore.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    NAME_PATTERN = r"<h1>(?P<N>.+?)<"
    SIZE_PATTERN = r"FILESIZE: (?P<S>[\d\.,]+) (?P<U>[\w^_]+)"
    OFFLINE_PATTERN = r">file not found<"

    def setup(self):
        self.chunk_limit = 1
        self.resume_download = True
        self.multi_dl = True

    def handle_free(self, pyfile):
        try:
            fid = re.search(r'wert="(.+?)"', self.data).group(1)

        except AttributeError:
            self.error(self._("File-ID not found"))

        self.link = self.load("http://mystore.to/api/download", post={"FID": fid})
