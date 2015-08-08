# -*- coding: utf-8 -*-

import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class HellshareCz(SimpleHoster):
    __name__    = "HellshareCz"
    __type__    = "hoster"
    __version__ = "0.86"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?hellshare\.(?:cz|com|sk|hu|pl)/[^?]*/\d+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Hellshare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    CHECK_TRAFFIC = True
    LOGIN_ACCOUNT = True

    NAME_PATTERN    = r'<h1 id="filename"[^>]*>(?P<N>[^<]+)</h1>'
    SIZE_PATTERN    = r'<strong id="FileSize_master">(?P<S>[\d.,]+)&nbsp;(?P<U>[\w^_]+)</strong>'
    OFFLINE_PATTERN = r'<h1>File not found.</h1>'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'<a href="([^?]+/(\d+)/\?do=(fileDownloadButton|relatedFileDownloadButton-\2)-showDownloadWindow)"'


    def setup(self):
        self.resume_download = self.multiDL = bool(self.account)
        self.chunk_limit = 1


getInfo = create_getInfo(HellshareCz)
