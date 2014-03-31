# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
############################################################################

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class PromptfileCom(SimpleHoster):
    __name__ = "PromptfileCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?promptfile\.com/"
    __version__ = "0.1"
    __description__ = """Promptfile.Com File Download Hoster"""
    __author_name__ = ("igel")

    FILE_INFO_PATTERN = r'<span style="[^"]*" title="[^"]*">(?P<N>.*?) \((?P<S>[\d.]+) (?P<U>\w+)\)</span>'
    FILE_OFFLINE_PATTERN = r'<span style="[^"]*" title="File Not Found">File Not Found</span>'

    CHASH_PATTERN = r'<input type="hidden" name="chash" value="([^"]*)" />'
    DIRECT_LINK_PATTERN = r"clip: {\s*url: '(https?://(?:www\.)promptfile[^']*)',"

    def handleFree(self):
        # STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.html)
        if not m:
            self.parseError("Unable to detect chash")
        chash = m.group(1)
        self.logDebug("read chash %s" % chash)
        # continue to stage2
        self.html = self.load(self.pyfile.url, decode=True, post={'chash': chash})

        # STAGE 2: get the direct link
        m = re.search(self.DIRECT_LINK_PATTERN, self.html, re.MULTILINE | re.DOTALL)
        if not m:
            self.parseError("Unable to detect direct link")
        direct = m.group(1)
        self.logDebug('found direct link: ' + direct)
        self.download(direct, disposition=True)


getInfo = create_getInfo(PromptfileCom)
