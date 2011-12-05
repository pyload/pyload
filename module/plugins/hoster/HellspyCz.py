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

class HellspyCz(SimpleHoster):
    __name__ = "HellspyCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*hellspy\.(?:cz|com|sk|hu)(/\S+/\d+)/?.*"
    __version__ = "0.24"
    __description__ = """HellSpy.cz"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = '<span class="filesize right">(?P<S>[0-9.]+) <span>(?P<U>[kKMG])i?B</span></span>\s*<h1>(?P<N>[^<]+)</h1>'
    FILE_OFFLINE_PATTERN = r'<h2>(404 - Page|File) not found</h2>'
    FILE_URL_REPLACEMENTS = [(r"http://(?:\w*\.)*hellspy\.(?:cz|com|sk|hu)(/\S+/\d+)/?.*", r"http://www.hellspy.com\1")]
    
    CREDIT_LEFT_PATTERN = r'<strong>Credits: </strong>\s*(\d+)'
    DOWNLOAD_AGAIN_PATTERN = r'<a id="button-download-start"[^>]*title="You can download the file without deducting your credit.">'
    DOWNLOAD_URL_PATTERN = r"launchFullDownload\('([^']+)'"

    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = 1

    def handleFree(self):
        self.fail("Only premium users can download from HellSpy.cz")

    def handlePremium(self):        
        # set PHPSESSID cookie
        cj = self.account.getAccountCookies(self.user)
        cj.setCookie(".hellspy.com", "PHPSESSID", self.account.phpsessid)
        self.logDebug("PHPSESSID: " + cj.getCookie("PHPSESSID"))

        info = self.account.getAccountInfo(self.user, True)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"]/1024))

        if self.pyfile.size / 1024 > info["trafficleft"]:
            self.logWarning("Not enough credit left to download file")

        # get premium download URL and download
        self.html = self.load(self.pyfile.url + "?download=1")
        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if not found: self.parseError("Download URL")
        url = found.group(1)
        self.logDebug("Download URL: " + url)
        self.download(url)

        info = self.account.getAccountInfo(self.user, True)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"]/1024))
        
getInfo = create_getInfo(HellspyCz)