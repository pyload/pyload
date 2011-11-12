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
        file_info = parseFileInfo(QuickshareCz, url, getURL(url, decode=True)) 
        result.append(file_info)
            
    yield result

class QuickshareCz(SimpleHoster):
    __name__ = "QuickshareCz"
    __type__ = "hoster"
    __pattern__ = r"http://.*quickshare.cz/stahnout-soubor/.*"
    __version__ = "0.51"
    __description__ = """Quickshare.cz"""
    __author_name__ = ("zoidberg")

    VAR_PATTERN = r"var ID1 = '(?P<ID1>[^']+)';var ID2 = '(?P<ID2>[^']+)';var ID3 = '(?P<ID3>[^']+)';var ID4 = '(?P<ID4>[^']+)';var ID5 = '[^']*';var UU_prihlasen = '[^']*';var UU_kredit = [^;]*;var velikost = [^;]*;var kredit_odecet = [^;]*;var CaptchaText = '(?P<CaptchaText>[^']+)';var server = '(?P<Server>[^']+)';"
    FILE_OFFLINE_PATTERN = r'<script type="text/javascript">location.href=\'/chyba\';</script>'
    FILE_SIZE_PATTERN = r'<br>Velikost: <strong>([0-9.]+)</strong>\s*(KB|MB|GB)<br>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        # marks the file as "offline" when the pattern was found on the html-page
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        # parse the name from the site and set attribute in pyfile
        parsed_vars = re.search(self.VAR_PATTERN, self.html)
        if parsed_vars is None:
            self.fail("Parser error")
        
        pyfile.name = parsed_vars.group('ID3')

        # download the file, destination is determined by pyLoad
        download_url = parsed_vars.group('Server') + "/download.php"
        self.log.debug("File:" + pyfile.name)
        self.log.debug("URL:" + download_url)

        self.download(download_url, post={
            "ID1": parsed_vars.group('ID1'),
            "ID2": parsed_vars.group('ID2'),
            "ID3": parsed_vars.group('ID3'),
            "ID4": parsed_vars.group('ID4')
        })

        # check download
        check = self.checkDownload({
            "no_slots": "obsazen na 100 %"
        })

        if check == "no_slots":
            self.retry(5, 600, "No free slots")
