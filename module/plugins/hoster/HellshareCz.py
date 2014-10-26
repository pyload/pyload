# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class HellshareCz(SimpleHoster):
    __name__ = "HellshareCz"
    __type__ = "hoster"
    __version__ = "0.83"

    __pattern__ = r'(http://(?:www\.)?hellshare\.(?:cz|com|sk|hu|pl)/[^?]*/\d+).*'

    __description__ = """Hellshare.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    FILE_NAME_PATTERN = r'<h1 id="filename"[^>]*>(?P<N>[^<]+)</h1>'
    FILE_SIZE_PATTERN = r'<strong id="FileSize_master">(?P<S>[\d.,]+)&nbsp;(?P<U>[\w^_]+)</strong>'
    OFFLINE_PATTERN = r'<h1>File not found.</h1>'
    SHOW_WINDOW_PATTERN = r'<a href="([^?]+/(\d+)/\?do=(fileDownloadButton|relatedFileDownloadButton-\2)-showDownloadWindow)"'


    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1


    def process(self, pyfile):
        if not self.account:
            self.fail(_("User not logged in"))
        pyfile.url = re.match(self.__pattern__, pyfile.url).group(1)
        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()
        if not self.checkTrafficLeft():
            self.fail(_("Not enough traffic left for user ") + self.user)

        m = re.search(self.SHOW_WINDOW_PATTERN, self.html)
        if m is None:
            self.error(_("SHOW_WINDOW_PATTERN not found"))

        self.url = "http://www.hellshare.com" + m.group(1)
        self.download(self.url)


getInfo = create_getInfo(HellshareCz)
