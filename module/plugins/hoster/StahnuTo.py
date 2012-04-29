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
    __pattern__ = r"http://(?:\w*\.)?stahnu.to/(?:files/get/|.*\?file=)(?P<ID>[^/]+).*"
    __version__ = "0.14"
    __description__ = """stahnu.to"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r"<td colspan='2'>N&aacute;zev souboru<br /><span>(?P<N>[^<]+)</span>"
    FILE_SIZE_PATTERN = r'<td>Velikost souboru<br /><span>(?P<S>[^<]+)\s*(?P<U>[kKMG])i?[Bb]</span></td>'
    FILE_OFFLINE_PATTERN = r'<!-- Obsah - start -->\s*<!-- Obsah - end -->'

    def setup(self):
        self.multiDL = True

    def process(self, pyfile):
        if not self.account:
            self.fail("Please enter your stahnu.to account")
               
        found = re.search(self.__pattern__, pyfile.url)
        file_id = found.group(1)

        self.html = self.load("http://www.stahnu.to/getfile.php?file=%s" % file_id, decode=True)              
        self.getFileInfo()
        
        if "K sta&#382;en&iacute; souboru se mus&iacute;te <strong>zdarma</strong> p&#345;ihl&aacute;sit!" in self.html:
            self.account.relogin(self.user)
            self.retry()

        self.download("http://www.stahnu.to/files/gen/" + file_id, post={
            "downloadbutton":	u"STÁHNOUT"
        })
