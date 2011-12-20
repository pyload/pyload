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

class EasybytezCom(SimpleHoster):
    __name__ = "EasybytezCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?easybytez.com/(\w+).*"
    __version__ = "0.01"
    __description__ = """easybytez.com"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    # shares code with TurbouploadCom

    FILE_NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>[^"]+)"'
    FILE_SIZE_PATTERN = r'You have requested <font color="red">[^<]+</font> \((?P<S>[^<]+)\)</font>'
    FILE_OFFLINE_PATTERN = r'<h2>File Not Found</h2>'
    
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]*)">'
    WAIT_PATTERN = r'<span id="countdown_str">[^>]*>(\d+)</span> seconds</span>'

    def handleFree(self):
        self.download(self.pyfile.url, post = self.getPostParameters(), ref = True, cookies = True)
        
    def getPostParameters(self):
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, self.html))
        self.logDebug(inputs)
        inputs['method_free'] = "Free Download"
        inputs['referer'] = self.pyfile.url
        if 'method_premium' in inputs: del inputs['method_premium'] 

        self.html = self.load(self.pyfile.url, post = inputs, ref = True, cookies = True)
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, self.html))
        self.logDebug(inputs)
        
        found = re.search(self.WAIT_PATTERN, self.html)
        self.setWait(int(found.group(1)) + 1 if found else 60)
        self.wait()
        
        return inputs

getInfo = create_getInfo(EasybytezCom)