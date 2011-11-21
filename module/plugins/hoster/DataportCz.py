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
    
class DataportCz(SimpleHoster):
    __name__ = "DataportCz"
    __type__ = "hoster"
    __pattern__ = r"http://.*dataport.cz/file/.*"
    __version__ = "0.33"
    __description__ = """Dataport.cz plugin - free only"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<h2 style="color: red;">(?P<N>[^<]+)</h2>'
    FILE_SIZE_PATTERN = r'<td>Velikost souboru:</td>\s*<td>(?P<S>[0-9.]+)(?P<U>[kKMG])i?B</td>'
    URL_PATTERN = r'<td><a href="([^"]+)"[^>]*class="ui-state-default button hover ui-corner-all "><strong>'
    NO_SLOTS_PATTERN = r'<td><a href="http://dataport.cz/kredit/"[^>]*class="ui-state-default button hover ui-corner-all ui-state-disabled">'
    FILE_OFFLINE_PATTERN = r'<h2>Soubor nebyl nalezen</h2>'
    
    def handleFree(self):
        if re.search(self.NO_SLOTS_PATTERN, self.html):
            self.setWait(900, True)
            self.wait()
            self.retry(12, 0, "No free slots")

        found = re.search(self.URL_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (URL)")
        download_url = found.group(1)

        self.download(download_url)

create_getInfo(DataportCz)