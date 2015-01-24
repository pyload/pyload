# -*- coding: utf-8 -*-

from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class HellshareCz(SimpleHoster):
    __name__    = "HellshareCz"
    __type__    = "hoster"
    __version__ = "0.85"

    __pattern__ = r'http://(?:www\.)?hellshare\.(?:cz|com|sk|hu|pl)/[^?]*/\d+'

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
        self.resumeDownload = self.multiDL = bool(self.account)
        self.chunkLimit = 1


getInfo = create_getInfo(HellshareCz)
