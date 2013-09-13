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
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns


class FastshareCz(SimpleHoster):
    __name__ = "FastshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?fastshare.cz/\d+/.+"
    __version__ = "0.17"
    __description__ = """FastShare.cz"""
    __author_name__ = ("zoidberg", "stickell")

    FILE_INFO_PATTERN = r'<h1 class="dwp">(?P<N>[^<]+)</h1>\s*<div class="fileinfo">\s*(?:Velikost|Size)\s*: (?P<S>[^,]+),'
    FILE_OFFLINE_PATTERN = ur'<td align=center>Tento soubor byl smazán'
    FILE_URL_REPLACEMENTS = [('#.*', '')]

    FREE_URL_PATTERN = r'action=(/free/.*?)>\s*<img src="([^"]*)"><br'
    PREMIUM_URL_PATTERN = r'(http://data\d+\.fastshare\.cz/download\.php\?id=\d+\&[^\s\"\'<>]+)'
    NOT_ENOUGH_CREDIC_PATTERN = "Nem.te dostate.n. kredit pro sta.en. tohoto souboru"

    def process(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.FILE_URL_REPLACEMENTS)
        self.req.setOption("timeout", 120)
        if self.premium and (not self.SH_CHECK_TRAFFIC or self.checkTrafficLeft()):
            self.handlePremium()
        else:
            self.html = self.load(pyfile.url, decode=not self.SH_BROKEN_ENCODING, cookies=self.SH_COOKIES)
            self.getFileInfo()
            self.handleFree()

    def handleFree(self):
        if u">100% FREE slotů je plných.<" in self.html:
            self.setWait(60, False)
            self.wait()
            self.retry(120, "No free slots")

        found = re.search(self.FREE_URL_PATTERN, self.html)
        if not found:
            self.parseError("Free URL")
        action, captcha_src = found.groups()
        captcha = self.decryptCaptcha("http://www.fastshare.cz/" + captcha_src)
        self.download("http://www.fastshare.cz/" + action, post={"code": captcha, "submit": u"stáhnout"})

        check = self.checkDownload({
            "paralell_dl":
            "<title>FastShare.cz</title>|<script>alert\('Pres FREE muzete stahovat jen jeden soubor najednou.'\)"
        })
        self.logDebug(self.req.lastEffectiveURL, self.req.lastURL, self.req.code)

        if check == "paralell_dl":
            self.setWait(600, True)
            self.wait()
            self.retry(6, "Paralell download")

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
