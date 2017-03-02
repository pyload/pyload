# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster


class BezvadataCz(SimpleHoster):
    __name__ = "BezvadataCz"
    __type__ = "hoster"
    __version__ = "0.35"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?bezvadata\.cz/stahnout/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """BezvaData.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<p><b>Soubor: (?P<N>.+?)</b></p>'
    SIZE_PATTERN = r'<li><strong>Velikost:</strong> (?P<S>.+?)</li>'
    OFFLINE_PATTERN = r'<title>BezvaData \| Soubor nenalezen</title>'

    def setup(self):
        self.resume_download = True
        self.multiDL = True

    def handle_free(self, pyfile):
        #: Download button
        m = re.search(r'<a class="stahnoutSoubor".*?href="(.*?)"', self.data)
        if m is None:
            self.error(_("Page 1 URL not found"))
        url = "http://bezvadata.cz%s" % m.group(1)

        #: Captcha form
        self.data = self.load(url)
        self.check_errors()

        action, inputs = self.parse_html_form('frm-stahnoutFreeForm')
        if not inputs:
            self.error(_("FreeForm"))

        m = re.search(r'<img src="data:image/png;base64,(.*?)"', self.data)
        if m is None:
            self.retry_captcha()

        inputs['captcha'] = self.captcha.decrypt_image(
            m.group(1).decode('base64'), input_type='png')

        #: Download url
        self.data = self.load("http://bezvadata.cz%s" % action, post=inputs)
        self.check_errors()
        m = re.search(r'<a class="stahnoutSoubor2" href="(.*?)">', self.data)
        if m is None:
            self.error(_("Page 2 URL not found"))
        url = "http://bezvadata.cz%s" % m.group(1)
        self.log_debug("DL URL %s" % url)

        #: countdown
        m = re.search(r'id="countdown">(\d\d):(\d\d)<', self.data)
        wait_time = (int(m.group(1)) * 60 + int(m.group(2))) if m else 120
        self.wait(wait_time, False)

        self.link = url

    def check_errors(self):
        if 'images/button-download-disable.png' in self.data:
            #: Parallel dl limit
            self.retry(5 * 60, 24, _("Download limit reached"))
        elif '<div class="infobox' in self.data:
            self.temp_offline()
        else:
            return SimpleHoster.check_errors(self)
