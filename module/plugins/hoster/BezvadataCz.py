# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class BezvadataCz(SimpleHoster):
    __name__    = "BezvadataCz"
    __type__    = "hoster"
    __version__ = "0.27"

    __pattern__ = r'http://(?:www\.)?bezvadata\.cz/stahnout/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """BezvaData.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<p><b>Soubor: (?P<N>[^<]+)</b></p>'
    SIZE_PATTERN = r'<li><strong>Velikost:</strong> (?P<S>[^<]+)</li>'
    OFFLINE_PATTERN = r'<title>BezvaData \| Soubor nenalezen</title>'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self, pyfile):
        #download button
        m = re.search(r'<a class="stahnoutSoubor".*?href="(.*?)"', self.html)
        if m is None:
            self.error(_("Page 1 URL not found"))
        url = "http://bezvadata.cz%s" % m.group(1)

        #captcha form
        self.html = self.load(url)
        self.checkErrors()
        for _i in xrange(5):
            action, inputs = self.parseHtmlForm('frm-stahnoutFreeForm')
            if not inputs:
                self.error(_("FreeForm"))

            m = re.search(r'<img src="data:image/png;base64,(.*?)"', self.html)
            if m is None:
                self.error(_("Wrong captcha image"))

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
            self.fail(_("No valid captcha code entered"))

        #download url
        self.html = self.load("http://bezvadata.cz%s" % action, post=inputs)
        self.checkErrors()
        m = re.search(r'<a class="stahnoutSoubor2" href="(.*?)">', self.html)
        if m is None:
            self.error(_("Page 2 URL not found"))
        url = "http://bezvadata.cz%s" % m.group(1)
        self.logDebug("DL URL %s" % url)

        #countdown
        m = re.search(r'id="countdown">(\d\d):(\d\d)<', self.html)
        wait_time = (int(m.group(1)) * 60 + int(m.group(2))) if m else 120
        self.wait(wait_time, False)

        self.link = url


    def checkErrors(self):
        if 'images/button-download-disable.png' in self.html:
            self.longWait(5 * 60, 24)  #: parallel dl limit
        elif '<div class="infobox' in self.html:
            self.tempOffline()
        else:
            return super(BezvadataCz, self).checkErrors()


    def loadcaptcha(self, data, *args, **kwargs):
        return data.decode('base64')


getInfo = create_getInfo(BezvadataCz)
