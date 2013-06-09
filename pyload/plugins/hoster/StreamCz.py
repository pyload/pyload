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
        
        html = getURL(url)
        if re.search(StreamCz.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            result.append((url, 0, 2, url))        
    yield result
    
class StreamCz(Hoster):
    __name__ = "StreamCz"
    __type__ = "hoster"
    __pattern__ = r"http://www.stream.cz/[^/]+/\d+.*"
    __version__ = "0.1"
    __description__ = """stream.cz"""
    __author_name__ = ("zoidberg")
   
    FILE_OFFLINE_PATTERN = r'<h1 class="commonTitle">Str.nku nebylo mo.n. nal.zt \(404\)</h1>'
    FILE_NAME_PATTERN = r'<link rel="video_src" href="http://www.stream.cz/\w+/(\d+)-([^"]+)" />'
    CDN_PATTERN = r'<param name="flashvars" value="[^"]*&id=(?P<ID>\d+)(?:&cdnLQ=(?P<cdnLQ>\d*))?(?:&cdnHQ=(?P<cdnHQ>\d*))?(?:&cdnHD=(?P<cdnHD>\d*))?&'

    def setup(self):
        self.multiDL = True
        self.resumeDownload = True

    def process(self, pyfile):     
        
        self.html = self.load(pyfile.url, decode=True)
        
        if re.search(self.FILE_OFFLINE_PATTERN, self.html): 
            self.offline()
        
        found = re.search(self.CDN_PATTERN, self.html)
        if found is None: self.fail("Parse error (CDN)")
        cdn = found.groupdict()
        self.logDebug(cdn)
        for cdnkey in ("cdnHD", "cdnHQ", "cdnLQ"):
            if cdn.has_key(cdnkey) and cdn[cdnkey] > '': 
                cdnid = cdn[cdnkey]
                break
        else:       
            self.fail("Stream URL not found")
            
        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None: self.fail("Parse error (NAME)")
        pyfile.name = "%s-%s.%s.mp4" % (found.group(2), found.group(1), cdnkey[-2:])
             
        download_url = "http://cdn-dispatcher.stream.cz/?id=" + cdnid
        self.logInfo("STREAM (%s): %s" % (cdnkey[-2:], download_url))
        self.download(download_url)         
