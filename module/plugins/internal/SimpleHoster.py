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

from module.plugins.Hoster import Hoster
from module.utils import html_unescape
from re import search

def parseFileInfo(self, url = '', html = ''):     
    if not html and hasattr(self, "html"): html = self.html
    name, size, status, found = '', 0, 0, 0
    
    if hasattr(self, "FILE_OFFLINE_PATTERN") and search(self.FILE_OFFLINE_PATTERN, html):
        # File offline
        status = 1
    elif hasattr(self, "FILE_INFO_PATTERN"):
        found = search(self.FILE_INFO_PATTERN, html)
        if found:
            name, size, units = found.groups()
    else:
        if hasattr(self, "FILE_NAME_PATTERN"):
            found = search(self.FILE_NAME_PATTERN, html)
            if found:
                name = found.group(1)
        
        if hasattr(self, "FILE_SIZE_PATTERN"):
            found = search(self.FILE_SIZE_PATTERN, html)    
            if found:
                size, units = found.groups()
                
    if size:
        # File online, return name and size
        for r in self.SIZE_REPLACEMENTS: 
            size = size.replace(r, self.SIZE_REPLACEMENTS[r])
        size = float(size) * 1024 ** self.SIZE_UNITS[units]
        status = 2
    
    if not name: name = url
                    
    return (name, size, status, url)

class PluginParseError(Exception):
    def __init__(self, msg):
        self.value = 'Parse error (%s) - plugin may be out of date' % msg
    def __str__(self):
        return repr(self.value)

class SimpleHoster(Hoster):
    __name__ = "SimpleHoster"
    __version__ = "0.1"
    __pattern__ = None
    __type__ = "hoster"
    __description__ = """Base hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    SIZE_UNITS = {'kB': 1, 'KB': 1, 'KiB': 1, 'MB': 2, 'MiB': 2, 'GB': 3, 'GiB': 3}
    SIZE_REPLACEMENTS = {',': '', ' ': ''}
       
    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False   

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode = True)
        self.getFileInfo()    
        if self.account:
            self.handlePremium()
        else:
            self.handleFree()
    
    def getFileInfo(self):
        self.logDebug("URL: %s" % self.pyfile.url)  
        name, size, status, url = parseFileInfo(self)           
        if status == 1: 
            self.offline()
        elif status == 0: 
            self.parseError('File info')
            
        if not name:
            name = html_unescape(urlparse(pyfile.url).path.split("/")[-1])    

        self.logDebug("FILE NAME: %s FILE SIZE: %s" % (name, size))        
        self.pyfile.name, self.pyfile.size = name, size
    
    def handleFree(self):
        self.fail("Free download not implemented")
        
    def handlePremium(self):
        self.fail("Premium download not implemented")
    
    def parseError(self, msg):
        raise PluginParseError(msg) 