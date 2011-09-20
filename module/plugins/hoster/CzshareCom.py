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
        if re.search(CzshareCom.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            found = re.search(CzshareCom.FILE_NAME_PATTERN, html)
            if found is not None:
                name = found.group(1)
                
                found = re.search(CzshareCom.FILE_SIZE_PATTERN, html)
                if found is not None:
                    size = float(found.group(1).replace(',','.'))
                    units = found.group(2)
                    pow = {'KiB': 1, 'MiB': 2, 'GiB': 3}[units]
                    size = int(size * 1024 ** pow)
                    result.append((name, size, 2, url))
                else:
                    result.append((name, 0, 2, url))
    yield result

class CzshareCom(Hoster):
    __name__ = "CzshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)*czshare\.(com|cz)/.*"
    __version__ = "0.7"
    __description__ = """CZshare.com"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_URL_PATTERN = r'<a href="([^"]+)" class="page-download">[^>]*alt="([^"]+)" /></a>'
    FORM_PATTERN = r'<form action="download.php" method="post">\s*<img src="captcha.php" id="captcha" />(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]+)"[^>]*/>'
    FILE_OFFLINE_PATTERN = r'<h2 class="red">[^<]*[Ss]oubor (nenalezen|expiroval|je po.kozen)[^<]*<span>&nbsp;</span></h2>'
    MULTIDL_PATTERN = r"<p><font color='red'>Z[^<]*PROFI.</font></p>"
    FILE_NAME_PATTERN = r'<h1>([^<]+)<span>&nbsp;</span></h1>'
    FILE_SIZE_PATTERN = r'<div class="tab" id="category">\s*Velikost:\s*([0-9.,]+)(KiB|MiB|GiB)\s*</div>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, cookies=True, decode=True)

        #marks the file as "offline" when the pattern was found on the html-page
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        # parse the name from the site and set attribute in pyfile
        found = re.search(self.FILE_URL_PATTERN, self.html)
        if found is None:
           self.fail("Parse error (URL)")

        pyfile.name = found.group(2)
        parsed_url = "http://czshare.com" + found.group(1)

        # get download ticket and parse html
        self.logDebug("PARSED_URL:" + parsed_url)
        self.logDebug("NAME:" + pyfile.name)
        self.html = self.load(parsed_url, cookies=True)

        #if not re.search(self.FORM_PATTERN, self.html):
        if re.search(self.MULTIDL_PATTERN, self.html):
           self.waitForFreeSlot()

        try:
            form = re.search(self.FORM_PATTERN, self.html, re.DOTALL).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
            pyfile.size = float(inputs['size'])/1024
        except Exception, e:
            self.logError(e)
            self.fail("Parse error (FORM)")
        
        # get and decrypt captcha
        captcha_url = 'http://czshare.com/captcha.php'
        inputs['captchastring2'] = self.decryptCaptcha(captcha_url)
        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + inputs['captchastring2'])

        # download the file, destination is determined by pyLoad
        self.download(parsed_url, cookies=True, post=inputs)

        # check download
        check = self.checkDownload({
            "tempoffline": re.compile(r"^Soubor je do.asn. nedostupn.$"),
            "multi_dl": re.compile(self.MULTIDL_PATTERN),
            "captcha_err": re.compile(self.FORM_PATTERN)
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