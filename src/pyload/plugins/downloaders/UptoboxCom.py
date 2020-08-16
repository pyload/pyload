# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class UptoboxCom(SimpleDownloader):
    __name__ = "UptoboxCom"
    __type__ = "downloader"
    __version__ = "0.36"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(uptobox|uptostream)\.com/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Uptobox.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    PLUGIN_DOMAIN = "uptobox.com"

    INFO_PATTERN = (
        r"""(?:"para_title">|<h1(?: .*)?>)(?P<N>.+) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)"""
    )
    OFFLINE_PATTERN = r"""(File not found|Access Denied|404 Not Found)"""
    TEMP_OFFLINE_PATTERN = r""">Service Unavailable"""
    WAIT_PATTERN = r"""data-remaining-time=["'](\d+)["']"""
    LINK_PATTERN = (
        r"""["'](https?://(?:obwp\d+\.uptobox\.com|\w+\.uptobox\.com/dl?)/.*?)["']"""
    )

    DL_LIMIT_PATTERN = r"""or you can wait (.+) to launch a new download"""
    URL_REPLACEMENTS = [("http://", "https://")]

    def setup(self):
        self.multi_dl = True
        self.chunk_limit = 1
        self.resume_download = True

    def handle_free(self, pyfile):
        m = re.search(
            r"""<input name=["']waitingToken["'] value=["'](.+?)["']""", self.data
        )
        if m is not None:
            self.data = self.load(
                pyfile.url, post={"waitingToken": m.group(1), "submit": "Free Download"}
            )

        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
