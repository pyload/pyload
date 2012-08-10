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

#shares code with WarserverCz

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.network.HTTPRequest import BadHeader
from module.utils import html_unescape

class CoolshareCz(SimpleHoster):
    __name__ = "CoolshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?coolshare.cz/stahnout/(?P<ID>\d+)/.+"
    __version__ = "0.12"
    __description__ = """CoolShare.cz"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = ur'<h1.*?>Stáhnout (?P<N>[^<]+)</h1>'
    FILE_SIZE_PATTERN = r'<li>Velikost: <strong>(?P<S>[^<]+)</strong>'
    FILE_OFFLINE_PATTERN = r'<h1>Soubor nenalezen</h1>'
    
    PREMIUM_URL_PATTERN = r'href="(http://[^/]+/dwn-premium.php.*?)"'
    DOMAIN = "http://csd01.coolshare.cz"
    
    SH_CHECK_TRAFFIC = True             
              
    def handleFree(self):
        try:      
            self.download("%s/dwn-free.php?fid=%s" % (self.DOMAIN, self.file_info['ID']))    
        except BadHeader, e:
            if e.code == 403:
                self.setWait(300, True)
                self.wait()
                self.retry(max_tries = 24, reason = "Download limit reached")
            else: raise
        
    def handlePremium(self):
        found = re.search(self.PREMIUM_URL_PATTERN, self.html)
        if not found: self.parseError("Premium URL")
        url = html_unescape(found.group(1))
        self.logDebug("Premium URL: " + url)        
        if not url.startswith("http://"): self.resetAccount()
        self.download(url)

getInfo = create_getInfo(CoolshareCz)