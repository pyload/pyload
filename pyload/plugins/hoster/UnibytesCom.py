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
from pycurl import FOLLOWLOCATION
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class UnibytesCom(SimpleHoster):
    __name__ = "UnibytesCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?unibytes\.com/[a-zA-Z0-9-._ ]{11}B"
    __version__ = "0.1"
    __description__ = """UniBytes.com"""
    __author_name__ = ("zoidberg")

    FILE_INFO_PATTERN = r'<span[^>]*?id="fileName"[^>]*>(?P<N>[^>]+)</span>\s*\((?P<S>\d.*?)\)'
    DOMAIN = 'http://www.unibytes.com'
    
    WAIT_PATTERN = r'Wait for <span id="slowRest">(\d+)</span> sec'
    DOWNLOAD_LINK_PATTERN = r'<a href="([^"]+)">Download</a>'

    def handleFree(self):
        action, post_data = self.parseHtmlForm('id="startForm"')                
        self.req.http.c.setopt(FOLLOWLOCATION, 0)
               
        for i in range(8):
            self.logDebug(action, post_data)
            self.html = self.load(self.DOMAIN + action, post = post_data)
            
            found = re.search(r'location:\s*(\S+)', self.req.http.header, re.I)
            if found:
                url = found.group(1)
                break
            
            if '>Somebody else is already downloading using your IP-address<' in self.html: 
                self.setWait(600, True)
                self.wait()
                self.retry()
                        
            if post_data['step'] == 'last':
                found = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
                if found:
                    url = found.group(1)
                    self.correctCaptcha()
                    break
                else:
                    self.invalidCaptcha()
            
            last_step = post_data['step']        
            action, post_data = self.parseHtmlForm('id="stepForm"')
            
            if last_step == 'timer':           
                found = re.search(self.WAIT_PATTERN, self.html)
                self.setWait(int(found.group(1)) if found else 60, False)
                self.wait()                
            elif last_step in ('captcha', 'last'):
                post_data['captcha'] = self.decryptCaptcha(self.DOMAIN + '/captcha.jpg')
        else:
            self.fail("No valid captcha code entered")             
                     
        self.logDebug('Download link: ' + url)
        self.req.http.c.setopt(FOLLOWLOCATION, 1)  
        self.download(url)        

getInfo = create_getInfo(UnibytesCom)