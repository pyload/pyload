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
from module.plugins.internal.DeadHoster import DeadHoster as SimpleHoster
   
"""
from module.network.RequestFactory import getURL

def getInfo(urls):
    for url in urls:
        file_id = re.search(UploadboxCom.__pattern__, url).group(1)
        html = getURL('http://uploadbox.com/files/%s/?ac=lang&lang_new=en' % file_id, decode = False) 
        file_info = parseFileInfo(UploadboxCom, url, html)
        yield file_info
"""

class UploadboxCom(SimpleHoster):
    __name__ = "Uploadbox"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploadbox\.com/files/([^/]+).*"
    __version__ = "0.05"
    __description__ = """UploadBox.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<p><span>File name:</span>\s*(?P<N>[^<]+)</p>'
    FILE_SIZE_PATTERN = r'<span>Size:</span>\s*(?P<S>[0-9.]+) (?P<U>[kKMG])i?B <span>'
    FILE_OFFLINE_PATTERN = r'<strong>File deleted from service</strong>'
    FILE_NAME_REPLACEMENTS = [(r"(.*)", lambda m: unicode(m.group(1), 'koi8_r'))]
    
    FREE_FORM_PATTERN = r'<form action="([^"]+)" method="post" id="free" name="free">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]+)" />'
    LIMIT_EXCEEDED_PATTERN = r'<strong>The limit of traffic for you is exceeded. Please </strong> <br />wait <strong>(\d+)</strong> minutes'
    DOWNLOAD_URL_PATTERN = r'<iframe id="file_download"[^>]*src="([^"]+)"></iframe>'

    def process(self, pyfile):
        self.file_id = re.search(self.__pattern__, pyfile.url).group(1)
        self.html = self.load('http://uploadbox.com/files/%s/?ac=lang&lang_new=en' % self.file_id, decode = False)
        self.getFileInfo()
        self.handleFree()

    def handleFree(self):
        # Solve captcha
        url = 'http://uploadbox.com/files/' + self.file_id       
        
        for i in range(5):
            self.html = self.load(url, post = {"free": "yes"})
            found = re.search(self.LIMIT_EXCEEDED_PATTERN, self.html)
            if found:
                self.setWait(int(found.group(1))*60, True)
                self.wait()
            else:
                break
        else:
            self.fail("Unable to get free download slot")
        
        for i in range(5):
            try:
                action, form = re.search(self.FREE_FORM_PATTERN, self.html, re.DOTALL).groups()
                inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
            except Exception, e:
                self.logError(e)
                self.fail("Parse error on page 2")
            
            captcha_url = 'http://uploadbox.com/?ac=captcha&code=' + inputs['code']          
            inputs['enter'] = self.decryptCaptcha(captcha_url)
            self.html = self.load('http://uploadbox.com/' + action, post = inputs)
            found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
            if found:
                self.correctCaptcha()
                download_url = found.group(1)
                break
            else:
                self.invalidCaptcha()
        else:
            self.fail("Incorrect captcha entered 5 times")

        # Download
        self.download(download_url)