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
    __pattern__ = r"http://(?:\w*\.)?easybytez.com/(\w{6,}).*"
    __version__ = "0.06"
    __description__ = """easybytez.com"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    # shares code with TurbouploadCom

    FILE_NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>[^"]+)"'
    FILE_SIZE_PATTERN = r'You have requested <font color="red">[^<]+</font> \((?P<S>[^<]+)\)</font>'
    FILE_INFO_PATTERN = r'<tr><td align=right><b>Filename:</b></td><td nowrap>(?P<N>[^<]+)</td></tr>\s*.*?<small>\((?P<S>[^<]+)\)</small>'    
    FILE_OFFLINE_PATTERN = r'<h2>File Not Found</h2>'
    
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)"[^>]*value="([^"]*)"'
    WAIT_PATTERN = r'<span id="countdown_str">[^>]*>(\d+)</span> seconds</span>'
    DIRECT_LINK_PATTERN = r'(http://(\w+\.easybytez\.com|\d+\.\d+\.\d+\.\d+)/files/\d+/\w+/[^"<]+)'

    FORM_PATTERN = r'<form name=["\']?%s[^>]*action=["\']?([^"\' ]+)(.*?)</form>'
    OVR_DOWNLOAD_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    OVR_KILL_LINK_PATTERN = r'<h2>Delete Link</h2>\s*<textarea[^>]*>([^<]+)'
    TEXTAREA_PATTERN = r"<textarea name='([^']+)'>([^<]+)</textarea>"
    
    HOSTER_URL = "www.easybytez.com" 

    def process(self, pyfile):
        if not re.match(self.__pattern__, self.pyfile.url):
            if self.premium:
                self.handleOverriden()
            else:
                self.fail("Only premium users can download from other hosters with %s" % self.HOSTER_URL)
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
        self.html = self.load(self.HOSTER_URL)
        action, form = re.search(self.FORM_PATTERN % "url", self.html, re.DOTALL).groups()
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        upload_id = "%012d" % int(random()*10**12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"  
        inputs['tos'] = '1'
        inputs['url_mass'] = self.pyfile.url
        inputs['up1oad_type'] = 'url'      
        
        self.logDebug(action, inputs)
        self.html = self.load(action, post = inputs)
        
        found = re.search(self.FORM_PATTERN % "F1", self.html, re.S | re.I)
        if not found:
            self.logDebug(self.html)
            self.fail("upload failed")
        action, form = found.groups()
                        
        inputs = dict(re.findall(self.TEXTAREA_PATTERN, form))
        if not inputs: parseError('TEXTAREA')
        self.logDebug(inputs) 
        if inputs['st'] == 'OK':
            self.html = self.load(action, post = inputs)
        else:
            self.fail(inputs['st'])
        
        found = re.search(self.OVR_DOWNLOAD_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK (OVR)')
        self.pyfile.url = found.group(1)
        self.retry()
        
    def downloadLink(self, link):           
        self.logDebug('DIRECT LINK: %s' % link) 
        self.download(link)  
                
    def getPostParameters(self, premium=False):
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, self.html))
        self.logDebug(inputs)
        
        if 'op' in inputs and inputs['op'] == 'download2': return inputs
        
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
    
    def urlParseFileName(self):
        return html_unescape(urlparse(self.pyfile.url).path.split("/")[-1])

getInfo = create_getInfo(EasybytezCom)