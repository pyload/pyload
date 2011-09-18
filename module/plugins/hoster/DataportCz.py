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
        if re.search(DataportCz.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            found = re.search(DataportCz.FILE_NAME_PATTERN, html)
            if found is not None:
                name = found.group(1)
                result.append((name, 0, 2, url))
    yield result


class DataportCz(Hoster):
    __name__ = "DataportCz"
    __type__ = "hoster"
    __pattern__ = r"http://.*dataport.cz/file/.*"
    __version__ = "0.3"
    __description__ = """dataport.cz"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<h2 style="color: red;">([^<]+)</h2>'
    URL_PATTERN = r'<td><a href="([^"]+)"[^>]*class="ui-state-default button hover ui-corner-all "><strong>'
    NO_SLOTS_PATTERN = r'<td><a href="http://dataport.cz/kredit/"[^>]*class="ui-state-default button hover ui-corner-all ui-state-disabled">'
    FILE_OFFLINE_PATTERN = r'<h2>Soubor nebyl nalezen</h2>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if re.search(self.FILE_OFFLINE_PATTERN, self.html):
            self.offline()

        if re.search(self.NO_SLOTS_PATTERN, self.html):
            self.setWait(900, True)
            self.wait()
            self.retry()

        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (NAME)")
        pyfile.name = found.group(1)

        found = re.search(self.URL_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (URL)")
        download_url = found.group(1)

        self.download(download_url)           
