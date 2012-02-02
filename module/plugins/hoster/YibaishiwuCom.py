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
from module.common.json_layer import json_loads

class YibaishiwuCom(SimpleHoster):
    __name__ = "YibaishiwuCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?(?:u\.)?115.com/file/(?P<ID>\w+)"
    __version__ = "0.11"
    __description__ = """115.com"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r"file_name: '(?P<N>[^']+)'"
    FILE_SIZE_PATTERN = r"file_size: '(?P<S>[^']+)'"
    FILE_OFFLINE_PATTERN = ur'<h3><i style="color:red;">哎呀！提取码不存在！不妨搜搜看吧！</i></h3>'
    
    AJAX_URL_PATTERN = r'(/\?ct=(pickcode|download)[^"\']+)'    
              
    def handleFree(self):
        found = re.search(self.AJAX_URL_PATTERN, self.html)
        if not found: self.parseError("AJAX URL")
        url = found.group(1)
        self.logDebug(('FREEUSER' if found.group(2) == 'download' else 'GUEST') + ' URL', url)
        
        response = json_loads(self.load("http://115.com" + url, decode = False))
        for mirror in (response['urls'] if 'urls' in response else response['data'] if 'data' in response else []): 
            try:
                url = mirror['url'].replace('\\','')
                self.logDebug("Trying URL: " + url)
                header = self.download(url)
                break
            except:
                continue
        else: self.fail('No working link found')

getInfo = create_getInfo(YibaishiwuCom)