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

class SpeedfileCz(SimpleHoster):
    __name__ = "SpeedFileCz"
    __type__ = "hoster"
    __pattern__ = r"http://speedfile.cz/.*"
    __version__ = "0.31"
    __description__ = """speedfile.cz"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<meta property="og:title" content="(?P<N>[^"]+)" />'
    FILE_SIZE_PATTERN = r'<strong><big>(?P<S>[0-9.]+) (?P<U>[kKMG])i?B'
    URL_PATTERN = r'<a id="request" class="caps" href="([^"]+)" rel="nofollow">'
    FILE_OFFLINE_PATTERN = r'<title>Speedfile \| 404'
    WAIT_PATTERN = r'"requestedAt":(\d+),"allowedAt":(\d+),"adUri"'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if re.search(self.FILE_OFFLINE_PATTERN, self.html):
            self.offline()

        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (NAME)")
        pyfile.name = found.group(1)

        found = re.search(self.URL_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (URL)")
        download_url = "http://speedfile.cz/" + found.group(1)

        self.html = self.load(download_url)
        self.logDebug(self.html)
        found = re.search(self.WAIT_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (WAIT)")
        self.setWait(int(found.group(2)) - int(found.group(1)))
        self.wait()

        self.download(download_url)           

create_getInfo(SpeedfileCz)