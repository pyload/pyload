# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class BezvadataCz(SimpleHoster):
    __name__ = "BezvadataCz"
    __type__ = "hoster"
    __version__ = "0.24"

    __pattern__ = r'http://(?:www\.)?bezvadata.cz/stahnout/.*'

    __description__ = """BezvaData.cz hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<p><b>Soubor: (?P<N>[^<]+)</b></p>'
    FILE_SIZE_PATTERN = r'<li><strong>Velikost:</strong> (?P<S>[^<]+)</li>'
    OFFLINE_PATTERN = r'<title>BezvaData \| Soubor nenalezen</title>'


    def setup(self):
        self.multiDL = self.resumeDownload = True

    def handleFree(self):
        #download button
        m = re.search(r'<a class="stahnoutSoubor".*?href="(.*?)"', self.html)
        if m is None:
            self.parseError("page1 URL")
        url = "http://bezvadata.cz%s" % m.group(1)

        #captcha form
        self.html = self.load(url)
        self.checkErrors()
        for _ in xrange(5):
            action, inputs = self.parseHtmlForm('frm-stahnoutFreeForm')
            if not inputs:
                self.parseError("FreeForm")

            m = re.search(r'<img src="data:image/png;base64,(.*?)"', self.html)
            if m is None:
                self.parseError("captcha img")

            #captcha image is contained in html page as base64encoded data but decryptCaptcha() expects image url
            self.load, proper_load = self.loadcaptcha, self.load
            try:
                inputs['captcha'] = self.decryptCaptcha(m.group(1), imgtype='png')
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
        m = re.search(r'<a class="stahnoutSoubor2" href="(.*?)">', self.html)
        if m is None:
            self.parseError("page2 URL")
        url = "http://bezvadata.cz%s" % m.group(1)
        self.logDebug("DL URL %s" % url)

        #countdown
        m = re.search(r'id="countdown">(\d\d):(\d\d)<', self.html)
        wait_time = (int(m.group(1)) * 60 + int(m.group(2)) + 1) if m else 120
        self.wait(wait_time, False)

        self.download(url)

    def checkErrors(self):
        if 'images/button-download-disable.png' in self.html:
            self.longWait(5 * 60, 24)  # parallel dl limit
        elif '<div class="infobox' in self.html:
            self.tempOffline()

    def loadcaptcha(self, data, *args, **kwargs):
        return data.decode("base64")


getInfo = create_getInfo(BezvadataCz)
