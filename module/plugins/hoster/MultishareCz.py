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
        try:
            html = getURL(url, decode=True)
        except Exception:
            result.append((url, 0, 1, url))
        else:
            if re.search(MultishareCz.OFFLINE_PATTERN, html):
                # File offline
                result.append((url, 0, 1, url))
            else:
                # Get file info
                found = re.search(MultishareCz.FILE_INFO_PATTERN, html)
                if found is not None:
                    name = found.group(1)
                    size = float(found.group(2))
                    units = found.group(3)

                    pow = {'KB': 1, 'MB': 2, 'GB': 3}[units]
                    size = int(size * 1024 ** pow)

                    result.append((name, size, 2, url))
    yield result


class MultishareCz(Hoster):
    __name__ = "MultishareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?multishare.cz/stahnout/.*"
    __version__ = "0.3"
    __description__ = """MultiShare.cz"""
    __author_name__ = ("zoidberg")

    FILE_ID_PATTERN = r'/stahnout/(\d+)/'
    FILE_INFO_PATTERN = ur'<ul class="no-padding"><li>Název: <strong>([^<]+)</strong></li><li>Velikost: <strong>([^&]+)&nbsp;([^<]+)</strong>'
    OFFLINE_PATTERN = ur'<h1>Stáhnout soubor</h1><p><strong>Požadovaný soubor neexistuje.</strong></p>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if re.search(self.OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        found = re.search(self.FILE_ID_PATTERN, pyfile.url)
        if found is None:
            self.fail("Parse error (ID)")
        file_id = found.group(1)

        found = re.search(self.FILE_INFO_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (NAME)")
        pyfile.name = found.group(1)

        self.download("http://www.multishare.cz/html/download_free.php", get={
            "ID": file_id
        })