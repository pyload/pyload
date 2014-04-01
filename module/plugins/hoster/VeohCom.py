# -*- coding: utf-8 -*-
############################################################################
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
############################################################################

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class VeohCom(SimpleHoster):
    __name__ = "VeohCom"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?veoh\.com/(tv/)?(watch|videos)/(?P<ID>v\w+)'
    __version__ = "0.1"
    __config__ = [("quality", "Low;High", "Quality", "High")]
    __description__ = """Veoh.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    FILE_NAME_PATTERN = r'<meta name="title" content="(?P<N>.*?)"'
    FILE_OFFLINE_PATTERN = r'>Sorry, we couldn\'t find the video you were looking for'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://www.veoh.com/watch/\g<ID>')]

    SH_COOKIES = [(".veoh.com", "lassieLocale", "en")]

    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = -1

    def handleFree(self):
        q = self.getConfig("quality")
        pattern = r'"fullPreviewHash%sPath":"(.+?)"' % q
        found = re.search(pattern, self.html)
        if found:
            self.pyfile.name += ".mp4"
            link = found.group(1).replace("\\", "")
            self.logDebug("Download link: " + link)
            self.download(link)
        else:
            self.fail("No %s quality video found" % q.lower())


getInfo = create_getInfo(VeohCom)
