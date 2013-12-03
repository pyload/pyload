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

    @author: zoidberg
"""

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import fixup


class NowDownloadEu(SimpleHoster):
    __name__ = "NowDownloadEu"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?nowdownload\.(ch|co|eu|sx)/(dl/|download\.php\?id=)(?P<ID>\w+)"
    __version__ = "0.05"
    __description__ = """NowDownloadCh"""
    __author_name__ = ("godofdream", "Walter Purcaro")
    __author_mail__ = ("", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'Downloading</span> <br> (?P<N>.*) (?P<S>[0-9,.]+) (?P<U>[kKMG])i?B </h4>'
    FILE_OFFLINE_PATTERN = r'(This file does not exist!)'
    FILE_TOKEN_PATTERN = r'"(/api/token\.php\?token=[a-z0-9]+)"'
    FILE_CONTINUE_PATTERN = r'"(/dl2/[a-z0-9]+/[a-z0-9]+)"'
    FILE_WAIT_PATTERN = r'\.countdown\(\{until: \+(\d+),'
    FILE_DOWNLOAD_LINK = r'"(http://f\d+\.nowdownload\.ch/dl/[a-z0-9]+/[a-z0-9]+/[^<>"]*?)"'

    FILE_NAME_REPLACEMENTS = [("&#?\w+;", fixup), (r'<[^>]*>', '')]

    def setup(self):
        self.multiDL = self.resumeDownload = True
        self.chunkLimit = -1

    def handleFree(self):
        tokenlink = re.search(self.FILE_TOKEN_PATTERN, self.html)
        continuelink = re.search(self.FILE_CONTINUE_PATTERN, self.html)
        if not tokenlink or not continuelink:
            self.fail('Plugin out of Date')

        found = re.search(self.FILE_WAIT_PATTERN, self.html)
        if found:
            wait = int(found.group(1))
        else:
            wait = 60

        baseurl = "http://www.nowdownload.ch"
        self.html = self.load(baseurl + str(tokenlink.group(1)))
        self.setWait(wait)
        self.wait()

        self.html = self.load(baseurl + str(continuelink.group(1)))

        url = re.search(self.FILE_DOWNLOAD_LINK, self.html)
        if not url:
            self.fail('Download Link not Found (Plugin out of Date?)')
        self.logDebug('Download link: ' + str(url.group(1)))
        self.download(str(url.group(1)))


getInfo = create_getInfo(NowDownloadEu)
