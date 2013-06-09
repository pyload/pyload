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
from module.plugins.internal.DeadHoster import DeadHoster as EasybytezCom, create_getInfo
#from module.plugins.internal.SimpleHoster import create_getInfo
#from module.plugins.hoster.EasybytezCom import EasybytezCom

class TurbouploadCom(EasybytezCom):
    __name__ = "TurbouploadCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?turboupload.com/(\w+).*"
    __version__ = "0.02"
    __description__ = """turboupload.com"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    # shares code with EasybytezCom
    
    DIRECT_LINK_PATTERN = r'<a href="(http://turboupload.com/files/[^"]+)">\1</a>'

    def handleFree(self):
        self.html = self.load(self.pyfile.url, post = self.getPostParameters(), ref = True, cookies = True)
        found = re.search(self.DIRECT_LINK_PATTERN, self.html)
        if not found: self.parseError('Download Link')
        url = found.group(1)
        self.logDebug('URL: ' + url)
        self.download(url)

getInfo = create_getInfo(TurbouploadCom)