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
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:

        html = getURL(url, decode=True)
        if re.search(LetitbitNet.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            found = re.search(r'<input[^>]* name="name" value="([^"]+)" />', html)
            if found is not None:
                name = found.group(1)
                found = re.search(r'<input[^>]* name="sssize" value="([^"]+)" />', html)
                if found is not None:
                    size = float(found.group(1))/1024
                    result.append((name, size, 2, url))
    yield result


class LetitbitNet(Hoster):
    __name__ = "LetitbitNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*letitbit.net/download/.*"
    __version__ = "0.1"
    __description__ = """letitbit.net"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    IFREE_FORM_PATTERN = r'<form id="ifree_form" action="([^"]+)" method="post">(.*?)</form>'
    DVIFREE_FORM_PATTERN = r'<form action="([^"]+)" method="post" id="dvifree">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="([^"]+)" value="([^"]+)" />'
    JS_SCRIPT_PATTERN = r'<title>[^<]*</title>\s*<script language="JavaScript">(.*?)</script>'
    JS_VARS_PATTERN = r"(\S+) = '?([^';]+)'?;"

    FILE_OFFLINE_PATTERN = r'<div id="download_content" class="hide-block">[^<]*<br>File not found<br /></div>'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        if re.search(self.FILE_OFFLINE_PATTERN, self.html): self.offline()

        try:
            action, form = re.search(self.IFREE_FORM_PATTERN, self.html, re.DOTALL).groups()
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
            pyfile.name = inputs['name']
            pyfile.size = float(inputs['sssize'])/1024
        except Exception, e:
            self.logError(e)
            self.fail("Parse error on page 1")

        self.html = self.load("http://letitbit.net"+action, post = inputs)
        try:
            action, form = re.search(self.DVIFREE_FORM_PATTERN, self.html, re.DOTALL).groups()
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        except Exception, e:
            self.logError(e)
            self.fail("Parse error on page 2")

        self.html = self.load(action, post = inputs)
        try:
            form = re.search(self.JS_SCRIPT_PATTERN, self.html, re.DOTALL).group(1)
            js_vars = dict(re.findall(self.JS_VARS_PATTERN, form))
            ajax_check_url = js_vars['ajax_check_url']
            self.setWait(int(js_vars['seconds'])+1)
            self.wait()
        except Exception, e:
            self.logError(e)
            self.fail("Parse error on page 3")

        download_url = self.load(ajax_check_url, post = inputs)
        self.download(download_url)