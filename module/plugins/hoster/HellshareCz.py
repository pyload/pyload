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
import datetime
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        file_info = parseFileInfo(HellshareCz, url, getURL(url, decode=True)) 
        result.append(file_info)
            
    yield result

class HellshareCz(SimpleHoster):
    __name__ = "HellshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:.*\.)*hellshare\.(?:cz|com|sk|hu)/[^?]*/(\d+).*"
    __version__ = "0.74"
    __description__ = """Hellshare.cz"""
    __author_name__ = ("zoidberg")

    FREE_URL_PATTERN = r'<form[^>]*action="(http://free\d*\.helldata[^"]*)"'
    PREMIUM_URL_PATTERN = r"launchFullDownload\('([^']*)'\);"
    FILE_NAME_PATTERN = r'<h1 id="filename">([^<]+)</h1>'
    FILE_SIZE_PATTERN = r'<td><span>Size</span></td>\s*<th><span>([0-9.]*)&nbsp;(kB|KB|MB|GB)</span></th>'
    FILE_OFFLINE_PATTERN = r'<h1>File not found.</h1>'
    CAPTCHA_PATTERN = r'<img class="left" id="captcha-img"src="([^"]*)" />'
    #FILE_CREDITS_PATTERN = r'<strong class="filesize">(\d+) MB</strong>'
    CREDIT_LEFT_PATTERN = r'<p>After downloading this file you will have (\d+) MB for future downloads.'
    DOWNLOAD_AGAIN_PATTERN = r'<p>This file you downloaded already and re-download is for free. </p>'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        if self.account:
            self.account.relogin(self.user)

        pyfile.url = re.search(r'([^?]*)', pyfile.url).group(1)
        self.html = self.load(pyfile.url, decode = True)
        self.getFileInfo()

        if "do=relatedFileDownloadButton" in self.html:
            found = re.search(self.__pattern__, self.pyfile.url)
            show_window = "relatedFileDownloadButton-%s-showDownloadWindow" % found.group(1)
        else:
            show_window = "fileDownloadButton-showDownloadWindow"
        self.html = self.load(pyfile.url, get = {"do" : show_window}, decode=True)

        if self.account:
            self.handlePremium()
        else:
            self.handleFree()

    def handleFree(self):
        # hellshare is very generous
        if "You exceeded your today's limit for free download. You can download only 1 files per 24 hours." in self.html:
            t = datetime.datetime.today().replace(hour=1, minute=0, second=0) + datetime.timedelta(
                days=1) - datetime.datetime.today()
            self.setWait(t.seconds, True)
            self.wait()
            self.retry()

        # parse free download url
        found = re.search(self.FREE_URL_PATTERN, self.html)
        if found is None: self.parseError("Free URL)")
        parsed_url = found.group(1)
        self.logDebug("Free URL: %s" % parsed_url)

        # decrypt captcha
        found = re.search(self.CAPTCHA_PATTERN, self.html)
        if found is None: self.parseError("Captcha")
        captcha_url = found.group(1)

        captcha = self.decryptCaptcha(captcha_url)
        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + captcha)
        
        self.download(parsed_url, post = {"captcha" : captcha, "submit" : "Download"})

        # check download
        check = self.checkDownload({
            "wrong_captcha": re.compile(self.FREE_URL_PATTERN)
        })

        if check == "wrong_captcha":
            self.invalidCaptcha()
            self.retry()

    def handlePremium(self):
        # get premium download url
        found = re.search(self.PREMIUM_URL_PATTERN, self.html)
        if found is None: self.fail("Parse error (URL)")
        download_url = found.group(1)

        # check credit
        if self.DOWNLOAD_AGAIN_PATTERN in self.html:
            self.logInfo("Downloading again for free")
        else:
            found = re.search(self.CREDIT_LEFT_PATTERN, self.html)
            if not found:
                self.logError("Not enough credit left: %d (%d needed). Trying to download as free user." % (credits_left, file_credits))
                self.resetAccount()
            credits_left = int(found.group(1))

            file_credits = ceil(self.pyfile.size / 1024 ** 2)
            self.logInfo("Downloading file for %d credits, %d credits left" % (file_credits, credits_left))

        self.download(download_url)

        info = self.account.getAccountInfo(self.user, True)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"] / 1024))