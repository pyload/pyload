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

    @author: jeix
"""

import re
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []
    
    for url in urls:
        
        html = getURL(url)
        if re.search(PutlockerCom.PATTERN_OFFLINE, html):
            result.append((url, 0, 1, url))
        else:
            name = re.search(PutlockerCom.PATTERN_FILENAME_1, html)
            if name is None:
                name = re.search(PutlockerCom.PATTERN_FILENAME_2, html)
            if name is None:
                result.append((url, 0, 1, url))
                continue
                
            name = name.group(1)
            
            # size = re.search(PutlockerCom.PATTERN_FILESIZE, html)
            # if size is None:
                # result.append((url, 0, 1, url))
                # continue
            
            # size = size.group(1)
            
            result.append((name, 0, 2, url))        
    yield result
    
class PutlockerCom(Hoster):
    __name__ = "PutlockerCom"
    __type__ = "hoster"
    __pattern__ = r'http://(www\.)?putlocker\.com/(file|embed)/[A-Z0-9]+'
    __version__ = "0.2"
    __description__ = """Putlocker.Com"""
    __author_name__ = ("jeix")
   
    PATTERN_OFFLINE    = r"This file doesn't exist, or has been removed."
    PATTERN_FILENAME_1 = "site-content.*?<h1>(.*?)<strong"
    PATTERN_FILENAME_2 = "<title>(.*?) \|"
    PATTERN_FILESIZE   = "site-content.*?<h1>.*?<strong>\\((.*?)\\)"
   
   
    def process(self, pyfile):   
        
        self.pyfile = pyfile
        self.html = self.load(pyfile.url, decode=True)
        
        if not self._checkOnline():
            self.offline()
        
        self.pyfile.name = self._getName()
        
        self.link = self._getLink()
        if not self.link.startswith('http://'):
            self.link = "http://www.putlocker.com" + self.link
        self.download( self.link )         

    def _checkOnline(self):
        if re.search(self.PATTERN_OFFLINE, self.html):
            return False
        else:
            return True
        
    def _getName(self):
        name = re.search(self.PATTERN_FILENAME_1, self.html)
        if name is None:
            name = re.search(self.PATTERN_FILENAME_2, self.html)
        # if name is None:
            # self.fail("%s: Plugin broken." % self.__name__)

        return name.group(1)
        
    def _getLink(self):
        self.hash = re.search("<input type=\"hidden\" value=\"([a-z0-9]+)\" name=\"hash\">", self.html)
        # if self.hash is None:
            # self.fail("%s: Plugin broken." % self.__name__)
            
        self.param = "hash=" + self.hash.group(1) + "&confirm=Continue+as+Free+User"
        self.html2 = self.load(self.pyfile.url, post=self.param)
        if ">You have exceeded the daily stream limit for your country\\. You can wait until tomorrow" in self.html2 or "(>This content server has been temporarily disabled for upgrades|Try again soon\\. You can still download it below\\.<)" in self.html2:
            self.waittime = 2 * 60 * 60
            self.retry(wait_time=self.waittime, reason="Waiting %s seconds" % self.waittime)
            
        self.link = re.search("<a href=\"/gopro\\.php\">Tired of ads and waiting\\? Go Pro\\!</a>[\t\n\rn ]+</div>[\t\n\rn ]+<a href=\"(/.*?)\"", self.html2)
        if self.link is None:
            self.link = re.search("\"(/get_file\\.php\\?download=[A-Z0-9]+\\&key=[a-z0-9]+)\"", self.html2)
        
        if self.link is None:
            self.link = re.search("\"(/get_file\\.php\\?download=[A-Z0-9]+\\&key=[a-z0-9]+&original=1)\"", self.html2)
            
        if self.link is None:
            self.link = re.search("playlist: \\'(/get_file\\.php\\?stream=[A-Za-z0-9=]+)\\'", self.html2)
            if not self.link is None:
                self.html3 = self.load("http://www.putlocker.com" + self.link.group(1))
                self.link = re.search("media:content url=\"(http://.*?)\"", self.html3)
                if self.link is None:
                    self.link = re.search("\"(http://media\\-b\\d+\\.putlocker\\.com/download/\\d+/.*?)\"", self.html3)
            
        # if link is None:
            # self.fail("%s: Plugin broken." % self.__name__)

        return self.link.group(1).replace("&amp;", "&")
         
        
