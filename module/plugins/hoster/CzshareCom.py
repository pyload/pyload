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
            file_info = parseFileInfo(CzshareCom, url, getURL(info_url, decode=True)) 
            result.append(file_info)
            
    yield result

class CzshareCom(SimpleHoster):
    __name__ = "CzshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)*czshare\.(com|cz)/(\d+/|download.php\?).*"
    __version__ = "0.88"
    __description__ = """CZshare.com"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<div class="tab" id="parameters">\s*<p>\s*Cel. n.zev: <a href=[^>]*>(?P<N>[^<]+)</a>'
    FILE_SIZE_PATTERN = r'<div class="tab" id="category">(?:\s*<p>[^\n]*</p>)*\s*Velikost:\s*(?P<S>[0-9., ]+)(?P<U>[kKMG])i?B\s*</div>'
    FILE_OFFLINE_PATTERN = r'<div class="header clearfix">\s*<h2 class="red">'
    FILE_SIZE_REPLACEMENTS = [(' ', '')]

    FREE_URL_PATTERN = r'<a href="([^"]+)" class="page-download">[^>]*alt="([^"]+)" /></a>'
    FREE_FORM_PATTERN = r'<form action="download.php" method="post">\s*<img src="captcha.php" id="captcha" />(.*?)</form>'
    PREMIUM_FORM_PATTERN = r'<form action="/profi_down.php" method="post">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]+)"[^>]*/>'
    MULTIDL_PATTERN = r"<p><font color='red'>Z[^<]*PROFI.</font></p>"
    USER_CREDIT_PATTERN = r'<div class="credit">\s*kredit: <strong>([0-9., ]+)([kKMG]i?B)</strong>\s*</div><!-- .credit -->'

    def setup(self):
        self.multiDL = self.resumeDownload = True if self.premium else False
        self.chunkLimit = 1

    def process(self, pyfile):
        url = toInfoPage(pyfile.url)
        if not url:
            self.logError(e)
            self.fail("Invalid URL")

        self.html = self.load(url, cookies=True, decode=True)
        self.getFileInfo()

        if not self.account or not self.handlePremium():
            self.handleFree()
        self.checkDownloadedFile()

    def handlePremium(self):
        # check if user logged in
        found = re.search(self.USER_CREDIT_PATTERN, self.html)
        if not found:
            self.account.relogin(self.user)
            self.html = self.load(self.pyfile.url, cookies=True, decode=True)
            found = re.search(self.USER_CREDIT_PATTERN, self.html)
            if not found: return False

        # check user credit
        try:
            credit = float(found.group(1).replace(',','.').replace(' ',''))
            credit = credit * 1024 ** {'KB': 0, 'MB': 1, 'GB': 2}[found.group(2)]
            self.logInfo("Premium download for %i KiB of Credit" % (self.pyfile.size / 1024))
            self.logInfo("User %s has %i KiB left" % (self.user, credit))
            if credit * 1024 < self.pyfile.size:
                self.logInfo("Not enough credit to download file %s" % self.pyfile.name)
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

    def handleFree(self):
        # get free url
        found = re.search(self.FREE_URL_PATTERN, self.html)
        if found is None:
           raise PluginParseError('Free URL')
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
            self.pyfile.size = int(inputs['size'])
        except Exception, e:
            self.logError(e)
            raise PluginParseError('Form')

        # get and decrypt captcha
        captcha_url = 'http://czshare.com/captcha.php'
        inputs['captchastring2'] = self.decryptCaptcha(captcha_url)
        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + inputs['captchastring2'])

        self.html = self.load(parsed_url, cookies=True, post=inputs)
        
        found = re.search("countdown_number = (\d+);", self.html)
        self.setWait(int(found.group(1)) if found else 50)

        # download the file, destination is determined by pyLoad
        self.logDebug("WAIT URL", self.req.lastEffectiveURL)        
        found = re.search("free_wait.php\?server=(.*?)&(.*)", self.req.lastEffectiveURL)        
        if not found:
            raise PluginParseError('Download URL')

        url = "http://%s/download.php?%s" % (found.group(1), found.group(2))
        
        self.wait() 
        self.multiDL = True           
        self.download(url)    

    def checkDownloadedFile(self):
        # check download
        check = self.checkDownload({
            "tempoffline": re.compile(r"^Soubor je do.asn. nedostupn.$"),
            "multi_dl": re.compile(self.MULTIDL_PATTERN),
            "captcha_err": "<li>Zadaný ověřovací kód nesouhlasí!</li>"
            })

        if check == "tempoffline":
            self.fail("File not available - try later")
        elif check == "multi_dl":
            self.waitForFreeSlot()
        elif check == "captcha_err":
            self.invalidCaptcha()
            self.retry()

    def waitForFreeSlot(self, wait_time = 300):
        self.multiDL = False
        self.setWait(wait_time, True)
        self.wait()
        self.retry()