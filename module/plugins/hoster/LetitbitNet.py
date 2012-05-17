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
from random import random
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.common.json_layer import json_loads

class LetitbitNet(SimpleHoster):
    __name__ = "LetitbitNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*(letitbit|shareflare).net/download/.*"
    __version__ = "0.19"
    __description__ = """letitbit.net"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    CHECK_URL_PATTERN = r"ajax_check_url\s*=\s*'((http://[^/]+)[^']+)';"
    SECONDS_PATTERN = r"seconds\s*=\s*(\d+);"
    
    FILE_INFO_PATTERN = r'<h1[^>]*>File:.*?<span>(?P<N>[^<]+)</span>.*?\[<span>(?P<S>[^<]+)</span>]</h1>'
    FILE_OFFLINE_PATTERN = r'>File not found<'
       
    DOMAIN = "http://letitbit.net"
    FILE_URL_REPLACEMENTS = [(r"(?<=http://)([^/]+)", "letitbit.net")]
    
    def setup(self):
        self.resumeDownload = self.multiDL = True

    def handleFree(self):
        action, inputs = self.parseHtmlForm('id="ifree_form"')
        if not action: self.parseError("page 1 / ifree_form")
        self.pyfile.size = float(inputs['sssize'])
        #self.logDebug(action, inputs)
        inputs['desc'] = ""

        self.html = self.load(self.DOMAIN + action, post = inputs, cookies = True)
        
        """
        action, inputs = self.parseHtmlForm('id="d3_form"')
        if not action: self.parseError("page 2 / d3_form")
        #self.logDebug(action, inputs)

        self.html = self.load(action, post = inputs, cookies = True)

        try:
            ajax_check_url, captcha_url = re.search(self.CHECK_URL_PATTERN, self.html).groups()
            found = re.search(self.SECONDS_PATTERN, self.html)
            seconds = int(found.group(1)) if found else 60
            self.setWait(seconds+1)
            self.wait()
        except Exception, e:
            self.logError(e)
            self.parseError("page 3 / js")
        """
        
        found = re.search(self.SECONDS_PATTERN, self.html)      
        seconds = int(found.group(1)) if found else 60
        self.setWait(seconds+1)
        self.wait()
        
        response = self.load("%s/ajax/download3.php" % self.DOMAIN, post = " ", cookies = True)
        if response != '1': self.parseError('Unknown response - ajax_check_url')
        
        for i in range(5):
            captcha = self.decryptCaptcha('%s/captcha_new.php?rand=%d' % (self.DOMAIN, random() * 100000), cookies = True)
            response = self.load('%s/ajax/check_captcha.php' % self.DOMAIN, post = {"code": captcha}, cookies = True)
            self.logDebug(response)
            if not response:
                self.invalidCaptcha()
            elif response.startswith('['):
                urls = json_loads(response)
                break  
            elif response.startswith('http://'):
                urls = [response]
                break
            else:
                self.parseError("Unknown response - captcha check")             
                
        else:
            self.fail("No valid captcha solution received")
        
        self.correctCaptcha()
        
        for download_url in urls:
            try:
                self.logDebug("Download URL", download_url)
                self.download(download_url)
                break
            except Exception, e:
                self.logError(e)
        else:
            self.fail("Download did not finish correctly")

getInfo = create_getInfo(LetitbitNet)