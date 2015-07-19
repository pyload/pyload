# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class BezvadataCz(SimpleHoster):
    __name__    = "BezvadataCz"
    __type__    = "hoster"
    __version__ = "0.28"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?bezvadata\.cz/stahnout/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """BezvaData.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<p><b>Soubor: (?P<N>[^<]+)</b></p>'
    SIZE_PATTERN = r'<li><strong>Velikost:</strong> (?P<S>[^<]+)</li>'
    OFFLINE_PATTERN = r'<title>BezvaData \| Soubor nenalezen</title>'


    def setup(self):
        self.resume_download = True
        self.multi_dl        = True


    def handle_free(self, pyfile):
        #: Download button
        m = re.search(r'<a class="stahnoutSoubor".*?href="(.*?)"', self.html)
        if m is None:
            self.error(_("Page 1 URL not found"))
        url = "http://bezvadata.cz%s" % m.group(1)

        #: Captcha form
        self.html = self.load(url)
        self.check_errors()
        for _i in xrange(5):
            action, inputs = self.parse_html_form('frm-stahnoutFreeForm')
            if not inputs:
                self.error(_("FreeForm"))

            m = re.search(r'<img src="data:image/png;base64,(.*?)"', self.html)
            if m is None:
                self.error(_("Wrong captcha image"))

            #: Captcha image is contained in html page as base64encoded data but decryptCaptcha() expects image url
            self.load, proper_load = self.loadcaptcha, self.load
            try:
                inputs['captcha'] = self.decrypt_captcha(m.group(1), imgtype='png')
            finally:
                self.load = proper_load

            if '<img src="data:image/png;base64' in self.html:
                self.invalid_captcha()
            else:
                self.correct_captcha()
                break
        else:
            self.fail(_("No valid captcha code entered"))

        #: Download url
        self.html = self.load("http://bezvadata.cz%s" % action, post=inputs)
        self.check_errors()
        m = re.search(r'<a class="stahnoutSoubor2" href="(.*?)">', self.html)
        if m is None:
            self.error(_("Page 2 URL not found"))
        url = "http://bezvadata.cz%s" % m.group(1)
        self.log_debug("DL URL %s" % url)

        #: countdown
        m = re.search(r'id="countdown">(\d\d):(\d\d)<', self.html)
        wait_time = (int(m.group(1)) * 60 + int(m.group(2))) if m else 120
        self.wait(wait_time, False)

        self.link = url


    def check_errors(self):
        if 'images/button-download-disable.png' in self.html:
            self.wait(5 * 60, 24, _("Download limit reached"))  #: Parallel dl limit
        elif '<div class="infobox' in self.html:
            self.temp_offline()
        else:
            return super(BezvadataCz, self).check_errors()


    def loadcaptcha(self, data, *args, **kwargs):
        return data.decode('base64')


getInfo = create_getInfo(BezvadataCz)
