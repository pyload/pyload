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

        html = getURL(url, decode=True)
        if re.search(EuroshareEu.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            result.append((url, 0, 2, url))
    yield result

class EuroshareEu(Hoster):
    __name__ = "EuroshareEu"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?euroshare.eu/file/.*"
    __version__ = "0.30"
    __description__ = """Euroshare.eu"""
    __author_name__ = ("zoidberg")

    URL_PATTERN = r'<a class="free" href="([^"]+)"></a>'
    FILE_OFFLINE_PATTERN = r'<h2>S.bor sa nena.iel</h2>'
    ERR_PARDL_PATTERN = r'<h2>Prebieha s.ahovanie</h2>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        if re.search(self.ERR_PARDL_PATTERN, self.html) is not None:
            self.waitForFreeSlot()

        found = re.search(self.URL_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (URL)")
        parsed_url = found.group(1)

        self.download(parsed_url, disposition=True)

    def waitForFreeSlot(self):
        self.setWait(300, True)
        self.wait()
        self.retry()