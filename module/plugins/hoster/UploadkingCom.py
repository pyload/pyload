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
        if re.search(UploadkingCom.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            name, size = url, 0

            found = re.search(UploadkingCom.FILE_INFO_PATTERN, html)
            if found is not None:
                name, size, units = found.groups()
                size = float(size) * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[units]
                result.append((name, size, 2, url))
    yield result

class UploadkingCom(Hoster):
    __name__ = "UploadkingCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploadking\.com/\w{10}"
    __version__ = "0.1"
    __description__ = """UploadKing.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r'<font style="font-size:\d*px;">File(?:name)?:\s*<(?:b|/font><font[^>]*)>([^<]+)(?:</b>)?</div></TD></TR><TR><TD[^>]*><font style="font-size:\d*px;">(?:Files|S)ize:\s*<(?:b|/font><font[^>]*)>([0-9.]+) (KB|MB|GB)</(?:b|font)>'
    FILE_OFFLINE_PATTERN = r'<center><font[^>]*>Unfortunately, this file is unavailable</font></center>'
    FILE_URL_PATTERN = r'id="dlbutton"><a href="([^"]+)"'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode = True)
        self.getFileInfo(pyfile)
        self.handleFree(pyfile)

    def getFileInfo(self, pyfile):
        if re.search(self.FILE_OFFLINE_PATTERN, self.html): self.offline()
        
        found = re.search(self.FILE_INFO_PATTERN, self.html)
        if not found: self.fail("Parse error (file info)")
        pyfile.name, size, units = found.groups()
        pyfile.size = float(size) * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[units]

    def handleFree(self, pyfile):                 
        found = re.search(self.FILE_URL_PATTERN, self.html) 
        if not found: self.fail("Captcha key not found")
        url = found.group(1)
            
        self.download(url)