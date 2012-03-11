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
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class FastshareCz(SimpleHoster):
    __name__ = "FastshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?fastshare.cz/\d+/.+"
    __version__ = "0.12"
    __description__ = """FastShare.cz"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<h3><b><span style=color:black;>(?P<N>[^<]+)</b></h3>'
    FILE_SIZE_PATTERN = r'<tr><td>Velikost: </td><td style=font-weight:bold>(?P<S>[^<]+)</td></tr>'
    FILE_OFFLINE_PATTERN = r'<div id="content">\s*<div style=background-color:white'
    SH_HTML_ENCODING = 'cp1250'

    FREE_URL_PATTERN = ur'<form method=post action=(/free/.*?)><b>Stáhnout FREE.*?<img src="([^"]*)">'

    def handleFree(self):
        found = re.search(self.FREE_URL_PATTERN, self.html)
        if not found: self.parseError("Free URL")
        action, captcha_src = found.groups()
        captcha = self.decryptCaptcha("http://www.fastshare.cz/" + captcha_src)
        self.download("http://www.fastshare.cz/" + action, post = {"code": captcha, "submit": u"stáhnout"})

        check = self.checkDownload({"paralell_dl": "<script>alert('Pres FREE muzete stahovat jen jeden soubor najednou.')"})
        self.logDebug(self.req.lastEffectiveURL, self.req.lastURL, self.req.code)

        if check == "paralell_dl":
            self.setWait(600, True)
            self.wait()
            self.retry()

getInfo = create_getInfo(FastshareCz)