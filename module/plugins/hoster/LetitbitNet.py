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

class LetitbitNet(SimpleHoster):
    __name__ = "LetitbitNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*letitbit.net/download/.*"
    __version__ = "0.12"
    __description__ = """letitbit.net"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FORM_PATTERN = r'<form%s action="([^"]+)" method="post"%s>(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]+)" />'
    CHECK_URL_PATTERN = r"ajax_check_url\s*=\s*'([^']+)';"
    SECONDS_PATTERN = r"seconds\s*=\s*(\d+);"
    
    FILE_INFO_PATTERN = r'<h1[^>]*>File: <a[^>]*><span>(?P<N>[^<]+)</span></a> [<span>(?P<S>[0-9.]+)\s*(?P<U>[kKMG])i?[Bb]</span>]</h1>'
    FILE_OFFLINE_PATTERN = r'<div id="download_content" class="hide-block">[^<]*<br>File not found<br /></div>'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        if re.search(self.FILE_OFFLINE_PATTERN, self.html): self.offline()

        try:
            action, form = re.search(self.FORM_PATTERN % (' id="ifree_form"', ''), self.html, re.DOTALL).groups()
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
            pyfile.name = inputs['name']
            pyfile.size = float(inputs['sssize'])/1024
        except Exception, e:
            self.logError(e)
            self.parseError("page 1 / ifree_form")

        #self.logDebug(inputs)
        inputs['desc'] = ""
        self.html = self.load("http://letitbit.net" + action, post = inputs)

        try:
            action, form = re.search(self.FORM_PATTERN % ('', ' id="d3_form"'), self.html, re.DOTALL).groups()
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        except Exception, e:
            self.logError(e)
            self.parseError("page 2 / d3_form")

        self.html = self.load(action, post = inputs)
        try:
            ajax_check_url = re.search(self.CHECK_URL_PATTERN, self.html).group(1)
            found = re.search(self.SECONDS_PATTERN, self.html)
            seconds = int(found.group(1)) if found else 60
            self.setWait(seconds+1)
            self.wait()
        except Exception, e:
            self.logError(e)
            self.parseError("page 3 / js")

        download_url = self.load(ajax_check_url, post = inputs)
        self.download(download_url)

getInfo = create_getInfo(LetitbitNet)