# -*- coding: utf-8 -*-

from ..internal.SimpleHoster import SimpleHoster


class HellshareCz(SimpleHoster):
    __name__ = "HellshareCz"
    __type__ = "hoster"
    __version__ = "0.91"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?hellshare\.(?:cz|com|sk|hu|pl)/[^?]*/\d+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Hellshare.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    CHECK_TRAFFIC = True
    LOGIN_ACCOUNT = True

    NAME_PATTERN = r'<h1 id="filename"[^>]*>(?P<N>[^<]+)</h1>'
    SIZE_PATTERN = r'<strong id="FileSize_master">(?P<S>[\d.,]+)&nbsp;(?P<U>[\w^_]+)</strong>'
    OFFLINE_PATTERN = r'<h1>File not found.</h1>'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'<a href="([^?]+/(\d+)/\?do=(fileDownloadButton|relatedFileDownloadButton-\2)-showDownloadWindow)"'

    def setup(self):
        self.resume_download = self.multiDL = bool(self.account)
        self.chunk_limit = 1
