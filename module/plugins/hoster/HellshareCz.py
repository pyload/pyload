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
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url, decode=True)
        if re.search(HellshareCz.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            found = re.search(HellshareCz.FILE_SIZE_PATTERN, html)
            if found is not None:
                size, units = found.groups()
                size = float(size) * 1024 ** {'kB': 1, 'KB': 1, 'MB': 2, 'GB': 3}[units]

            found = re.search(HellshareCz.FILE_NAME_PATTERN, html)
            if found is not None:
                name = found.group(1)

            if found or size > 0:
                result.append((name, 0, 2, url))
    yield result

class HellshareCz(Hoster):
    __name__ = "HellshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(.*\.)*hellshare\.(cz|com|sk|hu)/.*"
    __version__ = "0.70"
    __description__ = """Hellshare.cz"""
    __author_name__ = ("zoidberg")

    FREE_URL_PATTERN = r'<h3>I\'ll wait.*\s*<form action="([^"]*)"'
    PREMIUM_URL_PATTERN = r"launchFullDownload\('([^']*)'\);"
    FILE_NAME_PATTERN = r'<h1 id="filename">([^<]+)</h1>'
    FILE_SIZE_PATTERN = r'<td><span>Size</span></td>\s*<th><span>([0-9.]*)&nbsp;(kB|KB|MB|GB)</span></th>'
    FILE_OFFLINE_PATTERN = r'<h1>File not found.</h1>'
    CAPTCHA_PATTERN = r'<img class="left" id="captcha-img"src="([^"]*)" />'
    FILE_CREDITS_PATTERN = r'<strong class="filesize">(\d+) MB</strong>'
    CREDIT_LEFT_PATTERN = r'<p>After downloading this file you will have (\d+) MB for future downloads.'
    DOWNLOAD_AGAIN_PATTERN = r'<p>This file you downloaded already and re-download is for free. </p>'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        if self.account:
            self.account.relogin(self.user)

        pyfile.url = re.search(r'([^?]*)', pyfile.url).group(1)
        self.html = self.load(pyfile.url, get = {"do" : "fileDownloadButton-showDownloadWindow"}, decode=True)
        self.getFileInfo(pyfile)

        if self.account:
            self.handlePremium()
        else:
            self.handleFree()

    def getFileInfo(self, pyfile):
        #marks the file as "offline" when the pattern was found on the html-page
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        # parse the name from the site and set attribute in pyfile
        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (Filename")
        pyfile.name = found.group(1)

        found = re.search(self.FILE_SIZE_PATTERN, self.html)
        if found is not None:
            size, units = found.groups()
            pyfile.size = float(size) * 1024 ** {'kB': 1, 'KB': 1, 'MB': 2, 'GB': 3}[units]

    def handleFree(self):
        # hellshare is very generous
        if 'You exceeded your today's limit for free download. You can download only 1 files per 24 hours.' in self.html:
            t = datetime.datetime.today().replace(hour=1, minute=0, second=0) + datetime.timedelta(
                days=1) - datetime.datetime.today()
            self.setWait(t.seconds, True)
            self.wait()
            self.retry()

        # parse free download url
        found = re.search(self.FREE_URL_PATTERN, self.html)
        if found is None: self.fail("Parse error (URL)")
        parsed_url = found.group(1)
        self.logDebug("Free URL: %s" % parsed_url)

        # decrypt captcha
        found = re.search(self.CAPTCHA_PATTERN, self.html)
        if found is None: self.fail("Parse error (Captcha)")
        captcha_url = found.group(1)

        captcha = self.decryptCaptcha(captcha_url)
        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + captcha)

        self.download(parsed_url, post = {"captcha" : captcha, "submit" : "Download"})

        # check download
        check = self.checkDownload({
            "wrong_captcha": "<p>Incorrectly copied code from the image</p>"
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
                self.fail("Not enough credit left. Trying to download as free user.")
                self.resetAccount()
            credits_left = int(found.group(1))

            found = re.search(self.FILE_CREDITS_PATTERN, self.html)
            if found:
                self.file_credits = found.group(1)
            else:
                self.logError("Parse error: file credits")
                self.file_credits = "???"

            self.logInfo("Downloading file for %s credits, %d credits left" % (self.file_credits, credits_left))

        self.download(download_url)

        info = self.account.getAccountInfo(self.user, True)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"] / 1024))