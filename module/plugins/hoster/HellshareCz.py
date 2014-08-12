# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
"""

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class HellshareCz(SimpleHoster):
    __name__ = "HellshareCz"
    __type__ = "hoster"
    __pattern__ = r'(http://(?:www\.)?hellshare\.(?:cz|com|sk|hu|pl)/[^?]*/\d+).*'
    __version__ = "0.82"
    __description__ = """Hellshare.cz hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<h1 id="filename"[^>]*>(?P<N>[^<]+)</h1>'
    FILE_SIZE_PATTERN = r'<strong id="FileSize_master">(?P<S>[0-9.]*)&nbsp;(?P<U>[kKMG])i?B</strong>'
    OFFLINE_PATTERN = r'<h1>File not found.</h1>'
    SHOW_WINDOW_PATTERN = r'<a href="([^?]+/(\d+)/\?do=(fileDownloadButton|relatedFileDownloadButton-\2)-showDownloadWindow)"'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.fail("User not logged in")
        pyfile.url = re.match(self.__pattern__, pyfile.url).group(1)
        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()
        if not self.checkTrafficLeft():
            self.fail("Not enough traffic left for user %s." % self.user)

        m = re.search(self.SHOW_WINDOW_PATTERN, self.html)
        if m is None:
            self.parseError('SHOW WINDOW')
        self.url = "http://www.hellshare.com" + m.group(1)
        self.logDebug("DOWNLOAD URL: " + self.url)

        self.download(self.url)


getInfo = create_getInfo(HellshareCz)
