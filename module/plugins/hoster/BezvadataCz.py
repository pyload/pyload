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

class BezvadataCz(SimpleHoster):
    __name__ = "BezvadataCz"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)*bezvadata.cz/stahnout/.*"
    __version__ = "0.23"
    __description__ = """BezvaData.cz"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<p><b>Soubor: (?P<N>[^<]+)</b></p>'
    FILE_SIZE_PATTERN = r'<li><strong>Velikost:</strong> (?P<S>[^<]+)</li>'
    FILE_OFFLINE_PATTERN = r'<title>BezvaData \| Soubor nenalezen</title>'
    DOWNLOAD_FORM_PATTERN = r'<form class="download" action="([^"]+)" method="post" id="frm-stahnoutForm">'

    def handleFree(self):
        found = re.search(self.DOWNLOAD_FORM_PATTERN, self.html)
        if found is None: self.parseError("Download form")
        url = "http://bezvadata.cz" + found.group(1)
        self.logDebug("Download form: %s" % url)       
              
        self.download(url, post = {"stahnoutSoubor": "St%C3%A1hnout"}, cookies = True)

getInfo = create_getInfo(BezvadataCz)
        