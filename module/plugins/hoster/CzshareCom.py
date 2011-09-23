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

def toInfoPage(url):
    if r"/download.php?" in url:
        try:
            id = re.search(r"id=(\d+)", url).group(1)
            code = re.search(r"code=(\w+)", url).group(1)
        except Exception, e:
            return None
        return "http://czshare.com/%s/%s/" % (id, code)
    return url

def getInfo(urls):
    result = []

    for url in urls:
        info_url = toInfoPage(url)
        if info_url:
            html = getURL(info_url, decode=True)
            if re.search(CzshareCom.FILE_OFFLINE_PATTERN, html):
                # File offline
                result.append((url, 0, 1, url))
            else:
                # Get file info
                name, size = url, 0

                found = re.search(CzshareCom.FILE_SIZE_PATTERN, html)
                if found is not None:
                    size = float(found.group(1).replace(',','.').replace(' ',''))
                    units = found.group(2)
                    pow = {'KiB': 1, 'MiB': 2, 'GiB': 3}[units]
                    size = int(size * 1024 ** pow)

                found = re.search(CzshareCom.FILE_NAME_PATTERN, html)
                if found is not None:
                    name = found.group(1)

                if found or size > 0:
                    result.append((name, size, 2, url))
    yield result

class CzshareCom(Hoster):
    __name__ = "CzshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)*czshare\.(com|cz)/(\d+/|download.php\?).*"
    __version__ = "0.8"
    __description__ = """CZshare.com"""
    __author_name__ = ("zoidberg")

    FREE_URL_PATTERN = r'<a href="([^"]+)" class="page-download">[^>]*alt="([^"]+)" /></a>'
    FREE_FORM_PATTERN = r'<form action="download.php" method="post">\s*<img src="captcha.php" id="captcha" />(.*?)</form>'
    PREMIUM_FORM_PATTERN = r'<form action="/profi_down.php" method="post">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]+)"[^>]*/>'
    FILE_OFFLINE_PATTERN = r'<h2 class="red">[^<]*[Ss]oubor (nenalezen|expiroval|je po.kozen|byl smaz.n)[^<]*<span>&nbsp;</span></h2>'
    MULTIDL_PATTERN = r"<p><font color='red'>Z[^<]*PROFI.</font></p>"
    #FILE_NAME_PATTERN = r'<h1>([^<]+)<span>&nbsp;</span></h1>'
    FILE_NAME_PATTERN = r'<div class="tab" id="parameters">\s*<p>\s*Cel. n.zev: <a href=[^>]*>([^<]+)</a>'
    FILE_SIZE_PATTERN = r'<div class="tab" id="category">(?:\s*<p>[^\n]*</p>)*\s*Velikost:\s*([0-9., ]+)(KiB|MiB|GiB)\s*</div>'
    USER_CREDIT_PATTERN = r'<div class="credit">\s*kredit: <strong>([0-9., ]+)(KB|MB|GB)</strong>\s*</div><!-- .credit -->'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.premium else False
        self.chunkLimit = 1

    def process(self, pyfile):
        self.getFileInfo(pyfile)

        if self.premium and self.account is not None:
            for i in range(2):
                if self.handlePremium(pyfile): break
            else:
                self.resetAccount()
        else:
            self.handleFree(pyfile)
        self.checkDownloadedFile()

    def getFileInfo(self, pyfile):
        url = toInfoPage(pyfile.url)
        if not url:
            self.logError(e)
            self.fail("Invalid URL")

        self.html = self.load(url, cookies=True, decode=True)

        #marks the file as "offline" when the pattern was found on the html-page
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        # parse the name from the site and set attribute in pyfile
        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None:
           self.fail("Parse error (NAME)")
        pyfile.name = found.group(1)
        self.logDebug("NAME:" + pyfile.name)

        found = re.search(self.FILE_SIZE_PATTERN, self.html)
        if found is None:
            self.logError("Parse error (SIZE)")
        else:
            size = float(found.group(1).replace(',','.').replace(' ',''))
            pyfile.size = size * 1024 ** {'KiB': 1, 'MiB': 2, 'GiB': 3}[found.group(2)]

    def handlePremium(self, pyfile):
        # check user credit
        found = re.search(self.USER_CREDIT_PATTERN, self.html)
        if found is None:
            self.account.relogin(self.user)
            return False

        try:
            credit = float(found.group(1).replace(',','.').replace(' ',''))
            credit = credit * 1024 ** {'KB': 0, 'MB': 1, 'GB': 2}[found.group(2)]
            self.logInfo("Premium download for %i KiB of Credit" % (pyfile.size / 1024))
            self.logInfo("User %s has %i KiB left" % (self.user, credit))
            if credit * 1024 < pyfile.size:
                self.logInfo("Not enough credit to download file %s" % pyfile.name)
                self.resetAccount()
        except Exception, e:
            # let's continue and see what happens...
            self.logError('Parse error (CREDIT): %s' % e)

        # parse download link
        try:
            form = re.search(self.PREMIUM_FORM_PATTERN, self.html, re.DOTALL).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        except Exception, e:
            self.logError("Parse error (FORM): %s" % e)
            self.resetAccount()

        # download the file, destination is determined by pyLoad
        self.download("http://czshare.com/profi_down.php", cookies=True, post=inputs)
        return True

    def handleFree(self, pyfile):
        # get free url
        found = re.search(self.FREE_URL_PATTERN, self.html)
        if found is None:
           self.fail("Parse error (URL)")
        parsed_url = "http://czshare.com" + found.group(1)
        self.logDebug("PARSED_URL:" + parsed_url)

        # get download ticket and parse html
        self.html = self.load(parsed_url, cookies=True)

        #if not re.search(self.FREE_FORM_PATTERN, self.html):
        if re.search(self.MULTIDL_PATTERN, self.html):
           self.waitForFreeSlot()

        try:
            form = re.search(self.FREE_FORM_PATTERN, self.html, re.DOTALL).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
            pyfile.size = int(inputs['size'])
        except Exception, e:
            self.logError(e)
            self.fail("Parse error (FORM)")

        # get and decrypt captcha
        captcha_url = 'http://czshare.com/captcha.php'
        inputs['captchastring2'] = self.decryptCaptcha(captcha_url)
        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + inputs['captchastring2'])

        # download the file, destination is determined by pyLoad
        self.download(parsed_url, cookies=True, post=inputs)


    def checkDownloadedFile(self):
        # check download
        check = self.checkDownload({
            "tempoffline": re.compile(r"^Soubor je do.asn. nedostupn.$"),
            "multi_dl": re.compile(self.MULTIDL_PATTERN),
            "captcha_err": re.compile(self.FREE_FORM_PATTERN)
            })

        if check == "tempoffline":
            self.fail("File not available - try later")
        elif check == "multi_dl":
            self.waitForFreeSlot()
        elif check == "captcha_err":
            self.invalidCaptcha()
            self.retry()

    def waitForFreeSlot(self):
        self.setWait(900, True)
        self.wait()
        self.retry()