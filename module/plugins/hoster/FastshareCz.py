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

# Test links (random.bin):
# http://www.fastshare.cz/2141189/random.bin

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FastshareCz(SimpleHoster):
    __name__ = "FastshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?fastshare.cz/\d+/.+"
    __version__ = "0.21"
    __description__ = """FastShare.cz"""
    __author_name__ = ("zoidberg", "stickell")

    FILE_INFO_PATTERN = r'<h1 class="dwp">(?P<N>[^<]+)</h1>\s*<div class="fileinfo">\s*(?:Velikost|Size)\s*: (?P<S>[^,]+),'
    FILE_OFFLINE_PATTERN = '(?:The file  ?has been deleted|Requested page not found)'
    FILE_URL_REPLACEMENTS = [('#.*', '')]
    SH_COOKIES = [('fastshare.cz', 'lang', 'en')]

    FREE_URL_PATTERN = r'action=(/free/.*?)>\s*<img src="([^"]*)"><br'
    PREMIUM_URL_PATTERN = r'(http://data\d+\.fastshare\.cz/download\.php\?id=\d+\&[^\s\"\'<>]+)'
    NOT_ENOUGH_CREDIC_PATTERN = "Nem.te dostate.n. kredit pro sta.en. tohoto souboru"

    def handleFree(self):
        if '100% of FREE slots are full' in self.html:
            self.retry(120, 60, "No free slots")

        found = re.search(self.FREE_URL_PATTERN, self.html)
        if not found:
            self.parseError("Free URL")
        action, captcha_src = found.groups()
        captcha = self.decryptCaptcha("http://www.fastshare.cz" + captcha_src)
        self.download("http://www.fastshare.cz" + action, post={"code": captcha, "btn.x": 77, "btn.y": 18})

        check = self.checkDownload({
            "paralell_dl":
            "<title>FastShare.cz</title>|<script>alert\('Pres FREE muzete stahovat jen jeden soubor najednou.'\)",
            "wrong_captcha": "Download for FREE"
        })

        if check == "paralell_dl":
            self.retry(6, 10 * 60, "Paralell download")
        elif check == "wrong_captcha":
            self.retry(max_tries=5, reason="Wrong captcha")

    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)
        if 'location' in header:
            url = header['location']
        else:
            self.html = self.load(self.pyfile.url)
            self.getFileInfo()
            if self.NOT_ENOUGH_CREDIC_PATTERN in self.html:
                self.logWarning('Not enough traffic left')
                self.resetAccount()

            found = re.search(self.PREMIUM_URL_PATTERN, self.html)
            if not found:
                self.parseError("Premium URL")
            url = found.group(1)

        self.logDebug("PREMIUM URL: %s" % url)
        self.download(url, disposition=True)

        check = self.checkDownload({"credit": re.compile(self.NOT_ENOUGH_CREDIC_PATTERN)})
        if check == "credit":
            self.resetAccount()


getInfo = create_getInfo(FastshareCz)
