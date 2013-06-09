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

class EdiskCz(SimpleHoster):
    __name__ = "EdiskCz"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?edisk.(cz|sk|eu)/(stahni|sk/stahni|en/download)/.*"
    __version__ = "0.21"
    __description__ = """Edisk.cz"""
    __author_name__ = ("zoidberg")

    URL_PATTERN = r'<form name = "formular" action = "([^"]+)" method = "post">'
    FILE_INFO_PATTERN = r'<span class="fl" title="(?P<N>[^"]+)">\s*.*?\((?P<S>[0-9.]*) (?P<U>[kKMG])i?B\)</h1></span>'
    ACTION_PATTERN = r'/en/download/(\d+/.*\.html)'
    DLLINK_PATTERN = r'http://.*edisk.cz.*\.html'
    FILE_OFFLINE_PATTERN = r'<h3>This file does not exist due to one of the following:</h3><ul><li>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        url = re.sub("/(stahni|sk/stahni)/", "/en/download/", pyfile.url)

        self.logDebug('URL:' + url)

        found = re.search(self.ACTION_PATTERN, url)
        if found is None: self.parseError("ACTION")
        action = found.group(1)

        self.html = self.load(url, decode=True)
        self.getFileInfo()

        self.html = self.load(re.sub("/en/download/", "/en/download-slow/", url))

        url = self.load(re.sub("/en/download/", "/x-download/", url), post={
            "action": action
        })

        if not re.match(self.DLLINK_PATTERN, url):
            self.fail("Unexpected server response")

        self.download(url)

getInfo = create_getInfo(EdiskCz)        