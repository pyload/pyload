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
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        file_info = parseFileInfo(StahnuTo, url, getURL("http://stahnu.to/?file=" + re.search(StahnuTo.__pattern__, url).group(3), decode=True)) 
        result.append(file_info)
            
    yield result

class StahnuTo(SimpleHoster):
    __name__ = "StahnuTo"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?stahnu.to/(files/get/|.*\?file=)([^/]+).*"
    __version__ = "0.12"
    __description__ = """stahnu.to"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r"<div class='nadpis-01'><h2>(?<N>[^<]+)</h2></div>"
    FILE_SIZE_PATTERN = r'<td>Velikost souboru<br /><span>(?<S>[^<]+)\s*(?<U>[kKMG])i?[Bb]</span></td>'
    FILE_OFFLINE_PATTERN = r'<!-- Obsah - start -->\s*<!-- Obsah - end -->'
    #FILE_OFFLINE_PATTERN = r'<h2 align="center">Tento soubor neexistuje  nebo byl odstran&#283;n! </h2>'
    CAPTCHA_PATTERN = r'<img src="captcha/captcha.php" id="captcha" /></td>'

    def setup(self):
        self.multiDL = True

    def process(self, pyfile):
        found = re.search(self.__pattern__, pyfile.url)
        file_id = found.group(3)

        self.html = self.load("http://stahnu.to/?file=" + file_id, decode=True)
        self.getFileInfo()

        self.download("http://stahnu.to/files/gen/" + file_id, post={
            "file": file_id,
            "user": "Anonym",
            "commenttext": ""
        })
