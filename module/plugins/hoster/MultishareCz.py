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

class MultishareCz(SimpleHoster):
    __name__ = "MultishareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?multishare.cz/stahnout/.*"
    __version__ = "0.32"
    __description__ = """MultiShare.cz"""
    __author_name__ = ("zoidberg")

    FILE_ID_PATTERN = r'/stahnout/(\d+)/'
    FILE_INFO_PATTERN = ur'<ul class="no-padding"><li>Název: <strong>(?P<N>[^<]+)</strong></li><li>Velikost: <strong>(?P<S>[^&]+)&nbsp;(?P<U>[^<]+)</strong>'
    FILE_OFFLINE_PATTERN = ur'<h1>Stáhnout soubor</h1><p><strong>Požadovaný soubor neexistuje.</strong></p>'

    def handleFree(self):
        found = re.search(self.FILE_ID_PATTERN, pyfile.url)
        if found is None:
            self.fail("Parse error (ID)")
        file_id = found.group(1)

        self.download("http://www.multishare.cz/html/download_free.php", get={
            "ID": file_id
        })

getInfo = create_getInfo(MultishareCz)