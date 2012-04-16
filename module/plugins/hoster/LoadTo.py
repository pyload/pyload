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

    @author: halfman
"""

import re
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:

        html = getURL(url, decode=True)
        if re.search(LoadTo.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            name = re.search(LoadTo.FILE_NAME_PATTERN, html)
            size = re.search(LoadTo.SIZE_PATTERN, html)
            if name is not None and size is not None:
                name = name.group(1)
                size = size.group(1)
                result.append((name, size, 2, url))
    yield result

class LoadTo(Hoster):
    __name__ = "LoadTo"
    __type__ = "hoster"
    __pattern__ = r"http://(www.*?\.)?load\.to/.{7,10}?/.*" 
    __version__ = "0.1002"
    __description__ = """load.to"""
    __author_name__ = ("halfman")
    __author_mail__ = ("Pulpan3@gmail.com")

    FILE_NAME_PATTERN = r'<div class="toolarge"><h1>(.+?)</h1></div>'
    URL_PATTERN = r'<form method="post" action="(.+?)"'
    SIZE_PATTERN = r'<div class="download_table_right">(\d+) Bytes</div>'
    FILE_OFFLINE_PATTERN = r'Can\'t find file. Please check URL.<br />'
    WAIT_PATTERN = r'type="submit" value="Download \((\d+)\)"'

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
        download_url = found.group(1)
        
        timmy = re.search(self.WAIT_PATTERN, self.html)
        if timmy:
            self.setWait(timmy.group(1))
            self.wait()

        self.download(download_url)
