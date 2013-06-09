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
from pycurl import HTTPHEADER

class WrzucTo(SimpleHoster):
    __name__ = "WrzucTo"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w+\.)*?wrzuc\.to/([a-zA-Z0-9]+(\.wt|\.html)|(\w+/?linki/[a-zA-Z0-9]+))"
    __version__ = "0.01"
    __description__ = """Wrzuc.to plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    SH_COOKIES = [("http://www.wrzuc.to", "language", "en")]   
    FILE_SIZE_PATTERN = r'class="info">\s*<tr>\s*<td>(?P<S>.*?)</td>'
    FILE_NAME_PATTERN = r'id="file_info">\s*<strong>(?P<N>.*?)</strong>'
    
    def setup(self):
        self.multiDL = True 
    
    def handleFree(self):
        data = dict(re.findall(r'(md5|file): "(.*?)"', self.html))
        if len(data) != 2: self.parseError('File ID')
        
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = self.pyfile.url
        self.load("http://www.wrzuc.to/ajax/server/prepair", post = {"md5": data['md5']})
        
        self.req.http.lastURL = self.pyfile.url
        self.html = self.load("http://www.wrzuc.to/ajax/server/download_link", post = {"file": data['file']})
        
        data.update(re.findall(r'"(download_link|server_id)":"(.*?)"', self.html))
        if len(data) != 4: self.parseError('Download URL')
        
        download_url = "http://%s.wrzuc.to/pobierz/%s" % (data['server_id'], data['download_link'])       
        self.logDebug("Download URL: %s" % download_url)        
        self.download(download_url)
        
getInfo = create_getInfo(WrzucTo)

