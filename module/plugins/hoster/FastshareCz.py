# -*- coding: utf-8 -*-

###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: zoidberg
###############################################################################

# Test links (random.bin):
# http://www.fastshare.cz/2141189/random.bin

import re
from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FastshareCz(SimpleHoster):
    __name__ = "FastshareCz"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?fastshare\.cz/\d+/.+'
    __version__ = "0.22"
    __description__ = """FastShare.cz hoster plugin"""
    __author_name__ = ("zoidberg", "stickell", "Walter Purcaro")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'<h1 class="dwp">(?P<N>[^<]+)</h1>\s*<div class="fileinfo">\s*Size\s*: (?P<S>\d+) (?P<U>\w+),'
    FILE_OFFLINE_PATTERN = '>(The file has been deleted|Requested page not found)'

    FILE_URL_REPLACEMENTS = [("#.*", "")]
    SH_COOKIES = [(".fastshare.cz", "lang", "en")]

    FREE_URL_PATTERN = r'action=(/free/.*?)>\s*<img src="([^"]*)"><br'
    PREMIUM_URL_PATTERN = r'(http://data\d+\.fastshare\.cz/download\.php\?id=\d+&)'
    CREDIT_PATTERN = " credit for "

    def handleFree(self):
        if "> 100% of FREE slots are full" in self.html:
            self.retry(120, 60, "No free slots")

        found = re.search(self.FREE_URL_PATTERN, self.html)
        if found:
            action, captcha_src = found.groups()
        else:
            self.parseError("Free URL")

        baseurl = "http://www.fastshare.cz"
        captcha = self.decryptCaptcha(urljoin(baseurl, captcha_src))
        self.download(urljoin(baseurl, action), post={"code": captcha, "btn.x": 77, "btn.y": 18})

        check = self.checkDownload({
            "paralell_dl":
            "<title>FastShare.cz</title>|<script>alert\('Pres FREE muzete stahovat jen jeden soubor najednou.'\)",
            "wrong_captcha": "Download for FREE"
        })

        if check == "paralell_dl":
            self.retry(6, 600, "Paralell download")
        elif check == "wrong_captcha":
            self.retry(5, 1, "Wrong captcha")

    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)
        if "location" in header:
            url = header["location"]
        else:
            self.html = self.load(self.pyfile.url)

            self.getFileInfo()  #

            if self.CREDIT_PATTERN in self.html:
                self.logWarning("Not enough traffic left")
                self.resetAccount()
            else:
                found = re.search(self.PREMIUM_URL_PATTERN, self.html)
                if found:
                    url = found.group(1)
                else:
                    self.parseError("Premium URL")

        self.logDebug("PREMIUM URL: " + url)
        self.download(url, disposition=True)

        check = self.checkDownload({"credit": re.compile(self.CREDIT_PATTERN)})
        if check == "credit":
            self.resetAccount()


getInfo = create_getInfo(FastshareCz)
