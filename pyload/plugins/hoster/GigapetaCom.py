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
from random import randint
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from pycurl import FOLLOWLOCATION

class GigapetaCom(SimpleHoster):
    __name__ = "GigapetaCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?gigapeta\.com/dl/\w+"
    __version__ = "0.01"
    __description__ = """GigaPeta.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    SH_COOKIES = [("http://gigapeta.com", "lang", "us")]
    FILE_NAME_PATTERN = r'<img src=".*" alt="file" />-->\s*(?P<N>.*?)\s*</td>'
    FILE_SIZE_PATTERN = r'<th>\s*Size\s*</th>\s*<td>\s*(?P<S>.*?)\s*</td>'
    FILE_OFFLINE_PATTERN = r'<div id="page_error">'
    
    def handleFree(self):       
        captcha_key = str(randint(1,100000000))
        captcha_url = "http://gigapeta.com/img/captcha.gif?x=%s" % captcha_key
               
        self.req.http.c.setopt(FOLLOWLOCATION, 0)
        
        for i in range(5):
            self.checkErrors()
            
            captcha = self.decryptCaptcha(captcha_url)    
            self.html = self.load(self.pyfile.url, post = {
                "captcha_key": captcha_key, 
                "captcha": captcha,
                "download": "Download"})
            
            found = re.search(r"Location\s*:\s*(.*)", self.req.http.header, re.I)
            if found:
                download_url = found.group(1)                
                break          
            elif "Entered figures don&#96;t coincide with the picture" in self.html:
                self.invalidCaptcha()            
        else:
            self.fail("No valid captcha code entered")                  
        
        self.req.http.c.setopt(FOLLOWLOCATION, 1)
        self.logDebug("Download URL: %s" % download_url)
        self.download(download_url)
             
    def checkErrors(self):
        if "All threads for IP" in self.html:
            self.logDebug("Your IP is already downloading a file - wait and retry")
            self.setWait(300, True)
            self.wait()
            self.retry()
        
getInfo = create_getInfo(GigapetaCom)