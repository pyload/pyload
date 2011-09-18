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
                result.append((name, 0, 2, url))
    yield result


class CzshareCom(Hoster):
    __name__ = "CzshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://.*czshare\.(com|cz)/.*"
    __version__ = "0.6"
    __description__ = """CZshare.com"""
    __author_name__ = ("zoidberg")

    #FILE_URL_PATTERN = r'<a href="http://czshare.com/([^/]+)/([^/]+)/[^"]*">([^<]+)</a>'
    FILE_URL_PATTERN = r'<a href="([^"]+)" class="page-download">[^>]*alt="([^"]+)" /></a>'
    FORM_PATTERN = r'<form action="download.php" method="post">'
    ID_PATTERN = r'<input type="hidden" name="id" value="([^"]+)" />'
    FILE_PATTERN = r'<input type="hidden" name="file" value="([^"]+)" />'
    #TICKET_PATTERN = r'<input type="hidden" name="ticket" value="([^"]+)" />' 
    SUBMIT_PATTERN = r'<input type="submit" name="freedown" value="([^"]+)" class="button" />'
    SIZE_PATTERN = r'<input type="hidden" name="size" value="([^"]+)" />'
    SERVER_PATTERN = r'<input type="hidden" name="server" value="([^"]+)" />'
    FILE_OFFLINE_PATTERN = r'<h2 class="red">Soubor nenalezen<span>&nbsp;</span></h2>'
    MULTIDL_PATTERN = r"<p><font color='red'>Z[^<]*PROFI.</font></p>"
    FILE_NAME_PATTERN = r'<h1>([^<]+)<span>&nbsp;</span></h1>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

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
        self.html = self.load(parsed_url)

        #if not re.search(self.FORM_PATTERN, self.html):
        if re.search(self.MULTIDL_PATTERN, self.html):
            self.waitForFreeSlot()

        parse_err = False

        found = re.search(self.SERVER_PATTERN, self.html)
        if found is None:
            parse_err = True
            server = ""
        else:
            server = found.group(1)

        found = re.search(self.ID_PATTERN, self.html)
        if found is None:
            parse_err = True
            file_id = ""
        else:
            file_id = found.group(1)

        found = re.search(self.FILE_PATTERN, self.html)
        if found is None:
            parse_err = True
            long_id = ""
        else:
            long_id = found.group(1)

        found = re.search(self.SIZE_PATTERN, self.html)
        if found is None:
            parse_err = True
            size = ""
        else:
            size = found.group(1)

        self.logDebug("ID:" + file_id + " F:" + long_id + " B:" + size + " S:" + server)

        if parse_err:
            self.fail("Parse error")

        found = re.search(self.SUBMIT_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (SUBMIT)")
        else:
            submit = found.group(1)

            # get and decrypt captcha
        captcha_url = 'http://czshare.com/captcha.php'
        """
        if self.getConfig("randomCaptcha") == True:
           captcha = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(5))
        else:
        """
        captcha = self.decryptCaptcha(captcha_url)
        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + captcha)

        """
        self.setWait(self.getConfig("multiWait"), True)
        self.wait() 
        """

        # download the file, destination is determined by pyLoad
        #download_url = 'http://czshare.com/free.php'
        self.download(parsed_url, post={
            "id": file_id,
            "file": long_id,
            "size": size,
            "server": server,
            "captchastring2": captcha,
            "freedown": submit
        })

        # check download
        check = self.checkDownload({
            "tempoffline": re.compile(r"^Soubor je do.asn. nedostupn.$"),
            "multi_dl": re.compile(self.MULTIDL_PATTERN),
            "captcha_err": re.compile(self.SUBMIT_PATTERN)
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