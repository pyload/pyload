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
from module.common.json_layer import json_loads

class ExtabitCom(SimpleHoster):
    __name__ = "ExtabitCom"
    __type__ = "hoster"
    __pattern__ = r"http://(\w+\.)*extabit\.com/(file|go)/(?P<ID>\w+)"
    __version__ = "0.2"
    __description__ = """Extabit.com"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<th>File:</th>\s*<td class="col-fileinfo">\s*<div title="(?P<N>[^"]+)">'
    FILE_SIZE_PATTERN = r'<th>Size:</th>\s*<td class="col-fileinfo">(?P<S>[^<]+)</td>'
    FILE_OFFLINE_PATTERN = r'<h1>File not found</h1>'
    TEMP_OFFLINE_PATTERN = r">(File is temporary unavailable|No download mirror)<"
    
    DOWNLOAD_LINK_PATTERN = r'"(http://guest\d+\.extabit\.com/[a-z0-9]+/.*?)"'

    def handleFree(self):        
        if r">Only premium users can download this file" in self.html:
            self.fail("Only premium users can download this file")
        
        m = re.search(r"Next free download from your ip will be available in <b>(\d+)\s*minutes", self.html)
        if m:
            self.setWait(int(m.group(1)) * 60, True)
            self.wait()  
        elif "The daily downloads limit from your IP is exceeded" in self.html:
            self.setWait(3600, True)
            self.wait()
            
        self.logDebug("URL: " + self.req.http.lastEffectiveURL)
        m = re.match(self.__pattern__, self.req.http.lastEffectiveURL)
        fileID = m.group('ID') if m else self.file_info('ID')              
         
        m = re.search(r'recaptcha/api/challenge\?k=(\w+)', self.html)
        if m:
            recaptcha = ReCaptcha(self)
            captcha_key = m.group(1)
            
            for i in range(5):
                get_data = {"type": "recaptcha"}
                get_data["challenge"], get_data["capture"] = recaptcha.challenge(captcha_key)
                response = json_loads(self.load("http://extabit.com/file/%s/" % fileID, get = get_data))
                if "ok" in response:
                    self.correctCaptcha()
                    break
                else:
                    self.invalidCaptcha()
            else:
                self.fail("Invalid captcha")
        else:
            self.parseError('Captcha')
        
        if not "href" in response: self.parseError('JSON')
        
        self.html = self.load("http://extabit.com/file/%s%s" % (fileID, response['href']))
        m = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
        if not m:
            self.parseError('Download URL')
        url = m.group(1)
        self.logDebug("Download URL: " + url)
        self.download(url)      

getInfo = create_getInfo(ExtabitCom)