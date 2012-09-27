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
from module.plugins.ReCaptcha import ReCaptcha
from pycurl import FOLLOWLOCATION

class FilebeerInfo(SimpleHoster):
    __name__ = "FilebeerInfo"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?filebeer\.info/(?!\d*~f)(?P<ID>\w+).*"
    __version__ = "0.02"
    __description__ = """Filebeer.info plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'Filename:\s*</td>\s*<td>\s*(?P<N>.+?)&nbsp;&nbsp;'
    FILE_SIZE_PATTERN = r'Filesize:\s*</td>\s*<td>\s*(?P<S>[0-9.]+) (?P<U>[kKMG])i?B'
    FILE_INFO_PATTERN = r'<strong>\s*(?P<N>.+?) \((?P<S>[0-9.]+) (?P<U>[kKMG])i?B\)(<br/>\s*)?</strong>'
    FILE_OFFLINE_PATTERN = r'<title>Upload Files - FileBeer.info</title>'
    
    FILE_URL_REPLACEMENTS = [(__pattern__, 'http://filebeer.info/\g<ID>~i')]
    
    RECAPTCHA_KEY_PATTERN = r'http://www.google.com/recaptcha/api/(?:challenge|noscript)?k=(\w+)'
    DOWNLOAD_URL_PATTERN = r"\[url\](.+?)\[/url\]"
    WAIT_TIME_PATTERN = r"\(\'\.download-timer-seconds\'\)\.html\((\d+)\)"
    
    def setup(self):
        self.resumeDownload = True
        self.multiDL = self.premium
    
    def handleFree(self):
        url = self.getDownloadUrl()
         
        for i in range(5):
            self.html = self.load(url)            
            if i == 4 or 'id="form-join"' in self.html:
                break
            else:    
                found = re.search(self.WAIT_TIME_PATTERN, self.html)          
                self.setWait(int(found.group(1)) +1 if found else 61)
                self.wait()
                
        action, inputs = self.parseHtmlForm('form-join')
        if not action:
            self.fail('Form not found')          
    
        found = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
        recaptcha_key = found.group(1) if found else '6LeuAc4SAAAAAOSry8eo2xW64K1sjHEKsQ5CaS10'
        
        recaptcha = ReCaptcha(self)
        for i in range(5):               
            inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(recaptcha_key)            
            
            self.req.http.c.setopt(FOLLOWLOCATION, 0)
            self.html = self.load(action, post = inputs)
            self.header = self.req.http.header
            self.req.http.c.setopt(FOLLOWLOCATION, 1)
            
            found = re.search("Location\s*:\s*(.*)", self.header, re.I)
            if found:
                download_url = found.group(1).strip()
                self.correctCaptcha()
                break
            elif 'Captcha confirmation text is invalid' in self.html:
                self.invalidCaptcha()
            else:
                self.parseError('download url')
        
        else: self.fail("No valid captcha solution received")
        
        self.multiDL = True
        
        self.req.http.lastURL = action
        self.download(download_url)
    
    def handlePremium(self):        
        self.download(self.getDownloadUrl()) 
        
    def getDownloadUrl(self):
        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        return ("%s?d=1" % found.group(1)) if found else ("http://filebeer.info/%s?d=1" % self.file_info['ID'])           
        
getInfo = create_getInfo(FilebeerInfo)