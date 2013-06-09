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

#similar to coolshare.cz (down)

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.network.HTTPRequest import BadHeader
from module.utils import html_unescape

class WarserverCz(SimpleHoster):
    __name__ = "WarserverCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?warserver.cz/stahnout/(?P<ID>\d+)/.+"
    __version__ = "0.12"
    __description__ = """Warserver.cz"""
    __author_name__ = ("zoidberg")
    
    FILE_NAME_PATTERN = r'<h1.*?>(?P<N>[^<]+)</h1>'
    FILE_SIZE_PATTERN = r'<li>Velikost: <strong>(?P<S>[^<]+)</strong>'
    FILE_OFFLINE_PATTERN = r'<h1>Soubor nenalezen</h1>'
    
    PREMIUM_URL_PATTERN = r'href="(http://[^/]+/dwn-premium.php.*?)"'
    DOMAIN = "http://csd01.coolshare.cz"
    
    DOMAIN = "http://s01.warserver.cz"           
              
    def handleFree(self):
        try:      
            self.download("%s/dwn-free.php?fid=%s" % (self.DOMAIN, self.file_info['ID']))    
        except BadHeader, e:
            self.logError(e)
            if e.code == 403:
                self.longWait(60,60)
            else: raise
        self.checkDownloadedFile()
        
    def handlePremium(self):
        found = re.search(self.PREMIUM_URL_PATTERN, self.html)
        if not found: self.parseError("Premium URL")
        url = html_unescape(found.group(1))
        self.logDebug("Premium URL: " + url)        
        if not url.startswith("http://"): self.resetAccount()
        self.download(url)
        self.checkDownloadedFile()  
        
    def checkDownloadedFile(self):
        check = self.checkDownload({
            "offline": ">404 Not Found<"
            })

        if check == "offline":
            self.offline()     

getInfo = create_getInfo(WarserverCz)