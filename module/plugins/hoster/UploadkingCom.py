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
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        file_info = parseFileInfo(UploadkingCom, url, getURL(url, decode=False)) 
        result.append(file_info)
            
    yield result

class UploadkingCom(SimpleHoster):
    __name__ = "UploadkingCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploadking\.com/\w{10}"
    __version__ = "0.12"
    __description__ = """UploadKing.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r'<font style="font-size:\d*px;">File(?:name)?:\s*<(?:b|/font><font[^>]*)>([^<]+)(?:</b>)?</div></TD></TR><TR><TD[^>]*><font style="font-size:\d*px;">(?:Files|S)ize:\s*<(?:b|/font><font[^>]*)>([0-9.]+) ([kKMG]i?B)</(?:b|font)>'
    FILE_OFFLINE_PATTERN = r'<center><font[^>]*>Unfortunately, this file is unavailable</font></center>'
    FILE_URL_PATTERN = r'id="dlbutton"><a href="([^"]+)"'

    def handleFree(self):                 
        found = re.search(self.FILE_URL_PATTERN, self.html) 
        if not found: self.fail("Download URL not found")
        url = found.group(1)
        self.logDebug("DOWNLOAD URL: " + url)    
        self.download(url)