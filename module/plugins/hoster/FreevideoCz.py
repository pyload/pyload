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
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:

        html = getURL(url)
        if re.search(FreevideoCz.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            result.append((url, 0, 2, url))
    yield result

class FreevideoCz(Hoster):
    __name__ = "FreevideoCz"
    __type__ = "hoster"
    __pattern__ = r"http://www.freevideo.cz/vase-videa/(.*)\.html"
    __version__ = "0.1"
    __description__ = """freevideo.cz"""
    __author_name__ = ("zoidberg")

    URL_PATTERN = r'clip: {\s*url: "([^"]+)"'
    FILE_OFFLINE_PATTERN = r'<h2 class="red-corner-full">Str.nka nebyla nalezena</h2>'

    def setup(self):
        self.multiDL = True
        self.resumeDownload = True

    def process(self, pyfile):

        self.html = self.load(pyfile.url, decode=True)

        if re.search(self.FILE_OFFLINE_PATTERN, self.html):
           self.offline()

        found = re.search(self.URL_PATTERN, self.html)
        if found is None: self.fail("Parse error (URL)")
        download_url = found.group(1)

        pyfile.name = re.search(self.__pattern__, pyfile.url).group(1) + ".mp4"

        self.download(download_url)