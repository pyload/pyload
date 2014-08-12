# -*- coding: utf-8 -*-
###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FiredriveCom(SimpleHoster):
    __name__ = "FiredriveCom"
    __type__ = "hoster"
    __pattern__ = r'https?://(?:www\.)?(firedrive|putlocker)\.com/(mobile/)?(file|embed)/(?P<ID>\w+)'
    __version__ = "0.03"
    __description__ = """Firedrive.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    FILE_NAME_PATTERN = r'<b>Name:</b> (?P<N>.+) <br>'
    FILE_SIZE_PATTERN = r'<b>Size:</b> (?P<S>[\d.]+) (?P<U>[a-zA-Z]+) <br>'
    OFFLINE_PATTERN = r'class="sad_face_image"|>No such page here.<'
    TEMP_OFFLINE_PATTERN = r'>(File Temporarily Unavailable|Server Error. Try again later)'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://www.firedrive.com/file/\g<ID>')]

    LINK_PATTERN = r'<a href="(https?://dl\.firedrive\.com/\?key=.+?)"'


    def setup(self):
        self.multiDL = self.resumeDownload = True
        self.chunkLimit = -1

    def handleFree(self):
        link = self._getLink()
        self.logDebug("Direct link: " + link)
        self.download(link, disposition=True)

    def _getLink(self):
        f = re.search(self.LINK_PATTERN, self.html)
        if f:
            return f.group(1)
        else:
            self.html = self.load(self.pyfile.url, post={"confirm": re.search(r'name="confirm" value="(.+?)"', self.html).group(1)})
            f = re.search(self.LINK_PATTERN, self.html)
            if f:
                return f.group(1)
            else:
                self.parseError("Direct download link not found")


getInfo = create_getInfo(FiredriveCom)
