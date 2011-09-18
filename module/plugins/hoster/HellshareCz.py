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
            found = re.search(HellshareCz.FILE_NAME_PATTERN, html)
            if found is not None:
                name = found.group(1)
                result.append((name, 0, 2, url))
    yield result


class HellshareCz(Hoster):
    __name__ = "HellshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(.*\.)*hellshare\.(cz|com|sk|hu)/.*"
    __version__ = "0.6"
    __description__ = """Hellshare.cz"""
    __author_name__ = ("zoidberg")

    FREE_URL_PATTERN = r'<a id="button-download-free" href="([^"]*)"'
    PREMIUM_URL_PATTERN = r'<a onclick="return launchFullDownload[^>]*href="(http://[^/]+/([^/]+)/[^"]+)" target="full-download-iframe">'
    FILE_NAME_PATTERN = r'<strong id="FileName_master">([^<]+)</strong>'
    FILE_OFFLINE_PATTERN = r'<h1>Soubor nenalezen</h1>'
    SERVER_PATTERN = r'<form method="post" action="([^"]+)">'
    CAPTCHA_PATTERN = r'<p class="text-center marg-off"><img id="captcha-img" class="va-middle" src="([^"]+)"'
    FILE_CREDITS_PATTERN = r'<strong style="font-size:20px;">(\d+)\s*credits</strong>'
    CREDIT_LEFT_PATTERN = r'<a class="button-amount-1" href="[^>]*/buy-credit/" title="Your current credit">([^<]+)</a>'
    DOWNLOAD_AGAIN_PATTERN = r'Soubor jste ji. stahoval - opakovan. download prob.hne zdarma. Pokra.ovat'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        if self.premium and self.account is not None:
            self.account.relogin(self.user)
            self.getFileInfo(pyfile)
            self.handlePremium()
        else:
            self.getFileInfo(pyfile)
            self.handleFree()

    def getFileInfo(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        #marks the file as "offline" when the pattern was found on the html-page
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        # parse the name from the site and set attribute in pyfile       
        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (Filename")
        pyfile.name = found.group(1)

    def handleFree(self):
        # parse free download url
        found = re.search(self.FREE_URL_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (URL)")

        parsed_url = found.group(1)

        if parsed_url == "":
            t = datetime.datetime.today().replace(hour=1, minute=0, second=0) + datetime.timedelta(
                days=1) - datetime.datetime.today()
            self.setWait(t.seconds, True)
            self.wait()
            self.retry()

        # get download ticket and parse html
        self.logDebug("PARSED_URL:" + parsed_url)
        self.html = self.load(parsed_url)

        found = re.search(self.SERVER_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (Server)")
        download_url = found.group(1)

        found = re.search(self.CAPTCHA_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (Captcha)")
        captcha_url = found.group(1)

        # get and decrypt captcha
        captcha = self.decryptCaptcha(captcha_url)
        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + captcha)

        # download the file, destination is determined by pyLoad
        self.download(download_url, post={
            "captcha": captcha
        })

        # check download
        check = self.checkDownload({
            "wrong_captcha": "<p>Incorrectly copied code from the image</p>"
        })

        if check == "wrong_captcha":
            self.invalidCaptcha()
            self.retry()

    def handlePremium(self):
        found = re.search(self.FILE_CREDITS_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (Credits)")
        file_credits = int(found.group(1))

        found = re.search(self.CREDIT_LEFT_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (Credits left)")
        credits_left = int(found.group(1))

        self.logInfo("Premium download for %i credits" % file_credits)
        self.logInfo("User %s has %i credits left" % (self.user, credits_left))

        if file_credits > credits_left and not re.search(self.DOWNLOAD_AGAIN_PATTERN, self.html):
            self.resetAccount()

        found = re.search(self.PREMIUM_URL_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (URL)")
        download_url = found.group(1)

        self.download(download_url)

        info = self.account.getAccountInfo(self.user, True)
        self.logInfo("User %s has %i credits left" % (self.user, info["trafficleft"] / 1024))
        
            
            
        
