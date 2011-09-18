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
from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url, decode=True)
        if re.search(UloziskoSk.FILE_OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            # Get file info
            found = re.search(UloziskoSk.FILE_NAME_PATTERN, html)
            if found is not None:
                name = found.group(1)
                result.append((name, 0, 2, url))
    yield result


class UloziskoSk(Hoster):
    __name__ = "UloziskoSk"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?ulozisko.sk/.*"
    __version__ = "0.1"
    __description__ = """Ulozisko.sk"""
    __author_name__ = ("zoidberg")

    URL_PATTERN = r'<form name = "formular" action = "([^"]+)" method = "post">'
    ID_PATTERN = r'<input type = "hidden" name = "id" value = "([^"]+)" />'
    FILE_NAME_PATTERN = r'<input type = "hidden" name = "name" value = "([^"]+)" />'
    CAPTCHA_PATTERN = r'<img src="(/obrazky/obrazky.php\?fid=[^"]+)" alt="" />'
    FILE_OFFLINE_PATTERN = r'<span class = "red">Zadan� s�bor neexistuje z jedn�ho z nasleduj�cich d�vodov:</span>'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()

        found = re.search(self.URL_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (URL)")
        parsed_url = 'http://www.ulozisko.sk' + found.group(1)

        found = re.search(self.FILE_NAME_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (FILENAME)")
        pyfile.name = found.group(1)

        found = re.search(self.ID_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (ID)")
        id = found.group(1)

        self.logDebug('URL:' + parsed_url + ' NAME:' + pyfile.name + ' ID:' + id)

        found = re.search(self.CAPTCHA_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (CAPTCHA)")
        captcha_url = 'http://www.ulozisko.sk' + found.group(1)

        captcha = self.decryptCaptcha(captcha_url, cookies=True)

        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + captcha)

        self.download(parsed_url, post={
            "antispam": captcha,
            "id": id,
            "name": pyfile.name,
            "but": "++++STIAHNI+S%DABOR++++"
        })
        