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
from module.network.HTTPRequest import BadHeader

class WebshareCz(SimpleHoster):
    __name__ = "WebshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(\w+\.)?webshare.cz/(stahnout/)?(?P<ID>\w{10})-.+"
    __version__ = "0.11"
    __description__ = """WebShare.cz"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<h3>Stahujete soubor: </h3>\s*<div class="textbox">(?P<N>[^<]+)</div>'
    FILE_SIZE_PATTERN = r'<h3>Velikost souboru je: </h3>\s*<div class="textbox">(?P<S>[^<]+)</div>'
    FILE_OFFLINE_PATTERN = r'<h3>Soubor ".*?" nebyl nalezen.</h3>'
    
    DOWNLOAD_LINK_PATTERN = r'id="download_link" href="(?P<url>.*?)"'

    def handleFree(self):
        url_a = re.search(r"(var l.*)", self.html).group(1)
        url_b = re.search(r"(var keyStr.*)", self.html).group(1)        
        url = self.js.eval("%s\n%s\ndec(l)" % (url_a, url_b))
        
        self.logDebug('Download link: ' + url)
        self.download(url)        

getInfo = create_getInfo(WebshareCz)