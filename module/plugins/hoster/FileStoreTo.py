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

    @author: Walter Purcaro
"""

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileStoreTo(SimpleHoster):
    __name__ = "FileStoreTo"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?filestore\.to/\?d=(?P<ID>\w+)"
    __version__ = "0.01"
    __description__ = """FileStore.to download hoster"""
    __author_name__ = ("Walter Purcaro", "stickell")
    __author_mail__ = ("vuolter@gmail.com", "l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'File: <span[^>]*>(?P<N>.+)</span><br />Size: (?P<S>[\d,.]+) (?P<U>\w+)'
    FILE_OFFLINE_PATTERN = r'>Download-Datei wurde nicht gefunden<'

    def setup(self):
        self.resumeDownload = self.multiDL = True

    def handleFree(self):
        self.wait(10)
        ldc = re.search(r'wert="(\w+)"', self.html).group(1)
        link = self.load("http://filestore.to/ajax/download.php", get={"LDC": ldc})
        self.logDebug("Download link = " + link)
        self.download(link)


getInfo = create_getInfo(FileStoreTo)
