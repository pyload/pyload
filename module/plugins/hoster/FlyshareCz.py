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
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        file_info = parseFileInfo(FlyshareCz, url, getURL(url, decode=True)) 
        result.append(file_info)
            
    yield result

class FlyshareCz(SimpleHoster):
    __name__ = "FlyshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://.*flyshare.cz/stahni/.*"
    __version__ = "0.31"
    __description__ = """flyshare.cz"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<p><span class="filename">([^<]+)</span>'
    ERR_PATTERN = r'<p class="errorreport_error">Chyba: ([^<]+)</p>'
    FILE_OFFLINE_PATTERN = r'<p class="errorreport_error">Chyba: File is not available on the server</p>'

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        found = re.search(self.ERR_PATTERN, self.html)
        if found is not None:
            err_dsc = found.group(1)
            if err_dsc == "Too many simultaneous downloads, try again later":
                self.waitForFreeSlot()
            elif err_dsc == "File is not available on the server":
                self.offline()
            else:
                self.fail(err_dsc)

        self.getFileInfo()
        self.handleFree()

    def handleFree(self):
        self.download(self.pyfile.url, post={
            "wmod_command": "wmod_fileshare3:startDownload",
            "method": "free"
        })

        check = self.checkDownload({
            "sim_dl": '<p class="errorreport_error">Chyba: Too many simultaneous downloads, try again later</p>'
        })

        if check == "sim_dl":
            self.waitForFreeSlot()

    def waitForFreeSlot(self):
        self.setWait(600, True)
        self.wait()
        self.retry()
           
        
