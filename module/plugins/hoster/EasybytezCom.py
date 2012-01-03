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
from random import random

class EasybytezCom(SimpleHoster):
    __name__ = "EasybytezCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?easybytez.com/(\w+).*"
    __version__ = "0.03"
    __description__ = """easybytez.com"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    # shares code with TurbouploadCom

    FILE_NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>[^"]+)"'
    FILE_SIZE_PATTERN = r'You have requested <font color="red">[^<]+</font> \((?P<S>[^<]+)\)</font>'
    FILE_OFFLINE_PATTERN = r'<h2>File Not Found</h2>'
    
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]*)">'
    WAIT_PATTERN = r'<span id="countdown_str">[^>]*>(\d+)</span> seconds</span>'
    DIRECT_LINK_PATTERN = r'(http://\w+\.easybytez\.com/files/\d+/\w+/[^"<]+)'

    URL_FORM_PATTERN = r'<form name="url"[^>]*action="([^"]+)(.*?)</form>'
    OVR_DOWNLOAD_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    OVR_KILL_LINK_PATTERN = r'<h2>Delete Link</h2>\s*<textarea[^>]*>([^<]+)'

    def process(self, pyfile):
        if not re.match(self.__pattern__, self.pyfile.url):
            if self.premium:
                self.handleOverriden()
            else:
                self.fail("Only premium users can download from other hosters with EasyBytes")
        else:            
            self.html = self.load(pyfile.url, cookies = False, decode = True)
            self.file_info = self.getFileInfo()
            
            header = self.load(self.pyfile.url, just_header = True, cookies = True)
            self.logDebug(header)            
            
            if 'location' in header and re.match(self.DIRECT_LINK_PATTERN, header['location']):
                self.downloadLink(header['location'])
            elif self.premium:
                self.handlePremium()
            else:
                self.handleFree()
    
    def handleFree(self):
        self.download(self.pyfile.url, post = self.getPostParameters(), ref = True, cookies = True)
    
    def handlePremium(self):
        self.html = self.load(self.pyfile.url, post = self.getPostParameters(premium=True))
        found = re.search(self.DIRECT_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK')
        self.downloadLink(found.group(1))
    
    def handleOverriden(self):
        self.html = self.load('http://www.easybytez.com/')
        action, form = re.search(self.URL_FORM_PATTERN, self.html, re.DOTALL).groups()
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        action += "%d&js_on=1&utype=prem&upload_type=url" % int(random()*10**12)
        inputs['tos'] = '1'
        inputs['url_mass'] = self.pyfile.url
        
        self.html = self.load(action, post = inputs)
        found = re.search(self.OVR_DOWNLOAD_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK (OVR)')
        self.downloadLink(found.group(1))
        
    def downloadLink(self, link):           
        self.logDebug('DIRECT LINK: %s' % link) 
        self.download(link)  
                
    def getPostParameters(self, premium=False):
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, self.html))
        self.logDebug(inputs)
        inputs['referer'] = self.pyfile.url
        
        if premium:
            inputs['method_premium'] = "Premium Download"       
            if 'method_free' in inputs: del inputs['method_free'] 
        else:
            inputs['method_free'] = "Free Download"       
            if 'method_premium' in inputs: del inputs['method_premium'] 

        self.html = self.load(self.pyfile.url, post = inputs, ref = True, cookies = True)
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, self.html))
        self.logDebug(inputs)
        
        if not premium:
            found = re.search(self.WAIT_PATTERN, self.html)
            self.setWait(int(found.group(1)) + 1 if found else 60)
            self.wait()
        
        return inputs

getInfo = create_getInfo(EasybytezCom)