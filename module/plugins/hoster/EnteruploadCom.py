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
from module.plugins.internal.DeadHoster import DeadHoster as SimpleHoster, create_getInfo

class EnteruploadCom(SimpleHoster):
    __name__ = "EnteruploadCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?enterupload.com/\w+.*"
    __version__ = "0.02"
    __description__ = """EnterUpload.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r'<h3>(?P<N>[^<]+)</h3>\s*<span>File size:\s*(?P<S>[0-9.]+)\s*(?P<U>[kKMG])i?B</span>'
    FILE_OFFLINE_PATTERN = r'<(b|h2)>File Not Found</(b|h2)>|<font class="err">No such file with this filename</font>'
    TEMP_OFFLINE_PATTERN = r'>This server is in maintenance mode\. Refresh this page in some minutes\.<'   
    URL_REPLACEMENTS = [(r"(http://(?:www\.)?enterupload.com/\w+).*", r"\1")]
           
    FORM1_PATTERN = r'<form method="POST" action=\'\' style="display: none;">(.*?)</form>'
    FORM2_PATTERN = r'<form name="F1" method="POST"[^>]*>(.*?)</form>'
    FORM3_PATTERN = r'<form action="([^"]+)" method="get">'   
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]*)"[^>]*>'
    WAIT_PATTERN = r'<span id="countdown_str">Wait <[^>]*>(\d+)</span> seconds</span>'

    def handleFree(self):
        # Page 1
        try:
            form = re.search(self.FORM1_PATTERN, self.html, re.DOTALL).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        except Exception, e:
            self.logError(e)
            self.parseError("Form 1")   
        
        inputs['method_free'] =	'Free Download'
        self.logDebug(inputs)
        self.html = self.load(self.pyfile.url, post = inputs, decode = True, cookies = True, ref = True)

        # Page 2        
        try:
            form = re.search(self.FORM2_PATTERN, self.html, re.DOTALL).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        except Exception, e:
            self.logError(e)
            self.parseError("Form 2")
        
        inputs['method_free'] =	self.pyfile.url
        self.logDebug(inputs)
        
        found = re.search(self.WAIT_PATTERN, self.html)
        if found:
            self.setWait(int(found.group(1)) + 1)
            self.wait()
        
        self.html = self.load(self.pyfile.url, post = inputs, decode = True, cookies = True, ref = True)
        
        # Page 3
        found = re.search(self.FORM3_PATTERN, self.html)
        if not found: self.parseError("Form 3")
        url = found.group(1)
        
        # Download
        self.logDebug("Download URL: " + url)
        self.download(url, cookies = True, ref = True)

getInfo = create_getInfo(EnteruploadCom)