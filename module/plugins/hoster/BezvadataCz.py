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

class BezvadataCz(SimpleHoster):
    __name__ = "BezvadataCz"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)*bezvadata.cz/stahnout/.*"
    __version__ = "0.24"
    __description__ = """BezvaData.cz"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<p><b>Soubor: (?P<N>[^<]+)</b></p>'
    FILE_SIZE_PATTERN = r'<li><strong>Velikost:</strong> (?P<S>[^<]+)</li>'
    FILE_OFFLINE_PATTERN = r'<title>BezvaData \| Soubor nenalezen</title>'

    def setup(self):
        self.multiDL = self.resumeDownload = True

    def handleFree(self):
        #download button
        found = re.search(r'<a class="stahnoutSoubor".*?href="(.*?)"', self.html)
        if not found: self.parseError("page1 URL")
        url = "http://bezvadata.cz%s" % found.group(1)

        #captcha form
        self.html = self.load(url)
        self.checkErrors()
        for i in range(5):
            action, inputs = self.parseHtmlForm('frm-stahnoutFreeForm')
            if not inputs: self.parseError("FreeForm")

            found = re.search(r'<img src="data:image/png;base64,(.*?)"', self.html)
            if not found: self.parseError("captcha img")

            #captcha image is contained in html page as base64encoded data but decryptCaptcha() expects image url
            self.load, proper_load = self.loadcaptcha, self.load
            try:
                inputs['captcha'] = self.decryptCaptcha(found.group(1), imgtype='png')
            finally:
                self.load = proper_load

            if '<img src="data:image/png;base64' in self.html:
                self.invalidCaptcha()
            else:
                self.correctCaptcha()
                break
        else:
            self.fail("No valid captcha code entered")

        #download url
        self.html = self.load("http://bezvadata.cz%s" % action, post=inputs)
        self.checkErrors()
        found = re.search(r'<a class="stahnoutSoubor2" href="(.*?)">', self.html)
        if not found: self.parseError("page2 URL")
        url = "http://bezvadata.cz%s" % found.group(1)
        self.logDebug("DL URL %s" % url)

        #countdown
        found = re.search(r'id="countdown">(\d\d):(\d\d)<', self.html)
        wait_time = (int(found.group(1)) * 60 + int(found.group(2)) + 1) if found else 120
        self.setWait(wait_time, False)
        self.wait()

        self.download(url)

    def checkErrors(self):
        if 'images/button-download-disable.png' in self.html:
            self.longWait(300, 24) #parallel dl limit
        elif '<div class="infobox' in self.html:
            self.tempOffline()

    def loadcaptcha(self, data, *args, **kwargs):
        return data.decode("base64")

getInfo = create_getInfo(BezvadataCz)
