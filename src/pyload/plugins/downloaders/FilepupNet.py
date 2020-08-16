# -*- coding: utf-8 -*-

#
# Test links:
# http://www.filepup.net/files/k5w4ZVoF1410184283.html
# http://www.filepup.net/files/R4GBq9XH1410186553.html

import re

from ..base.simple_downloader import SimpleDownloader


class FilepupNet(SimpleDownloader):
    __name__ = "FilepupNet"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?filepup\.net/files/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filepup.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zapp-brannigan", "fuerst.reinje@web.de"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    NAME_PATTERN = r">(?P<N>.+?)</h1>"
    SIZE_PATTERN = r'class="fa fa-archive"></i> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r">This file has been deleted"

    LINK_FREE_PATTERN = r"(http://www\.filepup\.net/get/.+?)\'"

    def setup(self):
        self.multi_dl = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            dl_link = m.group(1)
            self.download(dl_link, post={"task": "download"})
