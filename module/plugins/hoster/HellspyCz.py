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
        file_info = parseFileInfo(HellspyCz, url, getURL(url, decode=True)) 
        result.append(file_info)
            
    yield result

class HellspyCz(SimpleHoster):
    __name__ = "HellspyCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*hellspy\.(?:cz|com|sk|hu)(/\S+/\d+)/?.*"
    __version__ = "0.21"
    __description__ = """HellSpy.cz"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<h1 class="text-yellow-1 " "><span ><span class="text" title="">([^<]+)</span></span></h1>'
    FILE_OFFLINE_PATTERN = r'<h2>(404 - Page|File) not found</h2>'
    FILE_CREDITS_PATTERN = r'<span class="text-credit-taken-1">\s*<span class="text-size"><span class="hidden">Size: </span>(\S+) (kB|MB|GB)</span>\s*<span >\((\d+) credits\)</span>'
    CREDIT_LEFT_PATTERN = r'<strong class="text-credits">(\d+)</strong>'

    PREMIUM_URL_PATTERN = r"launchFullDownload\('(http://[^']+)',\s*\d*\);"
    DOWNLOAD_AGAIN_PATTERN = r'<a id="button-download-start"[^>]*title="You can download the file without deducting your credit.">'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.premium: self.fail("Only premium users can download from HellSpy.cz")
        if not self.account: self.fail("Not logged in")

        # set PHPSESSID cookie
        cj = self.account.getAccountCookies(self.user)
        cj.setCookie(".hellspy.com", "PHPSESSID", self.account.phpsessid)
        self.logDebug("PHPSESSID: " + cj.getCookie("PHPSESSID"))

        info = self.account.getAccountInfo(self.user)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"]/1024))

        # load html
        rel_url = re.search(self.__pattern__, pyfile.url).group(1)
        self.html = self.load("http://www.hellspy.com/--%s-/%s" % (self.account.phpsessid, rel_url), decode = True)

        # get premium download URL
        download_url = self.getPremiumURL()
        if download_url is None:
            self.checkFile(pyfile)
            self.html = self.load("http://www.hellspy.com/%s?download=1" % rel_url)
            download_url = self.getPremiumURL()

        # download
        if download_url is None: self.fail("Parse error (DOWNLOAD URL)")
        self.logDebug("Download URL: " + download_url)
        self.download(download_url, disposition = True)

        info = self.account.getAccountInfo(self.user)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"]/1024))

    def checkFile(self, pyfile):
        # marks the file as "offline" when the pattern was found on the html-page
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        # parse the name from the site and set attribute in pyfile
        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None:
           self.fail("Parse error (FILENAME)")
        pyfile.name = found.group(1)

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


    def getPremiumURL(self):
        found = re.search(self.PREMIUM_URL_PATTERN, self.html)
        return found.group(1) if found else None