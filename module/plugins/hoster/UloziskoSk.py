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

class UloziskoSk(SimpleHoster):
    __name__ = "UloziskoSk"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?ulozisko.sk/.*"
    __version__ = "0.22"
    __description__ = """Ulozisko.sk"""
    __author_name__ = ("zoidberg")

    URL_PATTERN = r'<form name = "formular" action = "([^"]+)" method = "post">'
    ID_PATTERN = r'<input type = "hidden" name = "id" value = "([^"]+)" />'
    FILE_NAME_PATTERN = r'<div class="down1">(?P<N>[^<]+)</div>'
    FILE_SIZE_PATTERN = ur'Veľkosť súboru: <strong>(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</strong><br />'
    CAPTCHA_PATTERN = r'<img src="(/obrazky/obrazky.php\?fid=[^"]+)" alt="" />'
    FILE_OFFLINE_PATTERN = ur'<span class = "red">Zadaný súbor neexistuje z jedného z nasledujúcich dôvodov:</span>'
    IMG_PATTERN = ur'<strong>PRE ZVÄČŠENIE KLIKNITE NA OBRÁZOK</strong><br /><a href = "([^"]+)">'

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()
        
        found = re.search(self.IMG_PATTERN, self.html)
        if found:
            url = "http://ulozisko.sk" + found.group(1)
            self.download(url)
        else:
            self.handleFree()

    def handleFree(self):
        found = re.search(self.URL_PATTERN, self.html)
        if found is None: raise PluginParseError('URL')
        parsed_url = 'http://www.ulozisko.sk' + found.group(1)

        found = re.search(self.ID_PATTERN, self.html)
        if found is None: raise PluginParseError('ID')
        id = found.group(1)

        self.logDebug('URL:' + parsed_url + ' ID:' + id)

        found = re.search(self.CAPTCHA_PATTERN, self.html)
        if found is None: raise PluginParseError('CAPTCHA')
        captcha_url = 'http://www.ulozisko.sk' + found.group(1)

        captcha = self.decryptCaptcha(captcha_url, cookies=True)

        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + captcha)

        self.download(parsed_url, post={
            "antispam": captcha,
            "id": id,
            "name": self.pyfile.name,
            "but": "++++STIAHNI+S%DABOR++++"
        })

getInfo = create_getInfo(UloziskoSk)