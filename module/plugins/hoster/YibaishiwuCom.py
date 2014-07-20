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
"""

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.common.json_layer import json_loads


class YibaishiwuCom(SimpleHoster):
    __name__ = "YibaishiwuCom"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?(?:u\.)?115.com/file/(?P<ID>\w+)'
    __version__ = "0.12"
    __description__ = """115.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r"file_name: '(?P<N>[^']+)'"
    FILE_SIZE_PATTERN = r"file_size: '(?P<S>[^']+)'"
    OFFLINE_PATTERN = ur'<h3><i style="color:red;">哎呀！提取码不存在！不妨搜搜看吧！</i></h3>'

    LINK_PATTERN = r'(/\?ct=(pickcode|download)[^"\']+)'


    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.parseError("AJAX URL")
        url = m.group(1)
        self.logDebug(('FREEUSER' if m.group(2) == 'download' else 'GUEST') + ' URL', url)

        response = json_loads(self.load("http://115.com" + url, decode=False))
        if "urls" in response:
            mirrors = response['urls'] 
        elif "data" in response:
            mirrors = response['data']
        else:
            mirrors = None

        for mr in mirrors:
            try:
                url = mr['url'].replace("\\", "")
                self.logDebug("Trying URL: " + url)
                self.download(url)
                break
            except:
                continue
        else:
            self.fail('No working link found')


getInfo = create_getInfo(YibaishiwuCom)
