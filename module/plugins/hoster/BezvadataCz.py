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

class BezvadataCz(Hoster):
    __name__ = "BezvadataCz"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)*bezvadata.cz/stahnout/.*"
    __version__ = "0.2"
    __description__ = """BezvaData.cz"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    ID_PATTERN = r'<input type="hidden" name="souborId" value="([^"]+)">'
    HASH_PATTERN = r'<input type="hidden" name="souborHash" value="([^"]+)">'
    FILENAME_PATTERN = r'<title>BezvaData \| Stáhnout soubor ([^<]+)</title>'
    OFFLINE_PATTERN = r'<title>BezvaData \| Soubor nenalezen</title>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode = True)

        if re.search(self.OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        found = re.search(self.FILENAME_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (FILENAME)")
        pyfile.name = found.group(1)

        found = re.search(self.ID_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (ID)")
        souborId = found.group(1)

        found = re.search(self.HASH_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (HASH)")
        souborHash = found.group(1)

        self.logDebug("URL:"+pyfile.url+" ID:"+souborId+" HASH:"+souborHash)

        self.download(pyfile.url, post = {
            "souborId": souborId,
            "souborHash": souborHash,
            "_send": 'STAHNOUT SOUBOR'
        })