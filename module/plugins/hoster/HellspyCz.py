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
from math import ceil
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        file_info = parseFileInfo(HellspyCz, url, getURL(url, decode=True)) 
        result.append(file_info)
            
    yield result

class HellspyCz(SimpleHoster):
    __name__ = "HellspyCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*hellspy\.(?:cz|com|sk|hu)(/\S+/\d+)/?.*"
    __version__ = "0.22"
    __description__ = """HellSpy.cz"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = '<span class="filesize right">(?P<S>[0-9.]+) <span>(?P<U>[kKMG])i?B</span></span>\s*<h1>(?P<N>[^<]+)</h1>'
    FILE_OFFLINE_PATTERN = r'<h2>(404 - Page|File) not found</h2>'
    CREDIT_LEFT_PATTERN = r'<strong>Credits: </strong>\s*(\d+)'
    PREMIUM_URL_PATTERN = r'<a href="([^"]+)" class="ajax button button-blue button-download"'
    DOWNLOAD_AGAIN_PATTERN = r'<a id="button-download-start"[^>]*title="You can download the file without deducting your credit.">'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account: self.fail("Only premium users can download from HellSpy.cz")

        # set PHPSESSID cookie
        cj = self.account.getAccountCookies(self.user)
        cj.setCookie(".hellspy.com", "PHPSESSID", self.account.phpsessid)
        self.logDebug("PHPSESSID: " + cj.getCookie("PHPSESSID"))

        info = self.account.getAccountInfo(self.user)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"]/1024))

        # load html
        rel_url = re.search(self.__pattern__, pyfile.url).group(1)
        self.html = self.load("http://www.hellspy.com/--%s-/%s" % (self.account.phpsessid, rel_url), decode = True)
        
        self.getFileInfo()

        # get premium download URL and download
        found = re.search(self.PREMIUM_URL_PATTERN, self.html)
        if not found: self.parseError('Download URL')
        download_url = "http://www.hellspy.cz" + found.group(1)
        self.logDebug("Download URL: " + download_url)
        self.download(download_url, disposition = True)

        info = self.account.getAccountInfo(self.user)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"]/1024))

        """
        # parse credits left info
        found = re.search(self.CREDIT_LEFT_PATTERN, self.html)
        if found is None:
            self.logInfo("Not logged in... relogin and retry")
            self.account.relogin(self.user)
            self.retry(max_tries = 2, reason = "Not logged in")
        credits_left = int(found.group(1))
        self.logInfo("User %s has %i credits left" % (self.user, credits_left))

        # parse credit needed to proceed
        found = re.search(self.DOWNLOAD_AGAIN_PATTERN, self.html)
        if found:
            self.logInfo("Free download (file downloaded before)")
        else:
            found = re.search(self.FILE_CREDITS_PATTERN, self.html)
            if found is None: self.fail("Parse error (FILE CREDITS)")
            file_credits = int(found.group(3))
            if file_credits > credits_left: self.fail("Not enough credits left to download file")
            self.logInfo("Premium download for %i credits" % file_credits)
        """
