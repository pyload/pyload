# -*- coding: utf-8 -*-

import re

from pycurl import FOLLOWLOCATION
from random import randint

from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class GigapetaCom(SimpleHoster):
    __name__    = "GigapetaCom"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?gigapeta\.com/dl/\w+'

    __description__ = """GigaPeta.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<img src=".*" alt="file" />-->\s*(?P<N>.*?)\s*</td>'
    SIZE_PATTERN = r'<th>\s*Size\s*</th>\s*<td>\s*(?P<S>.*?)\s*</td>'
    OFFLINE_PATTERN = r'<div id="page_error">'

    COOKIES = [("gigapeta.com", "lang", "us")]


    def handleFree(self):
        captcha_key = str(randint(1, 100000000))
        captcha_url = "http://gigapeta.com/img/captcha.gif?x=%s" % captcha_key

        self.req.http.c.setopt(FOLLOWLOCATION, 0)

        for _i in xrange(5):
            self.checkErrors()

            captcha = self.decryptCaptcha(captcha_url)
            self.html = self.load(self.pyfile.url, post={
                "captcha_key": captcha_key,
                "captcha": captcha,
                "download": "Download"})

            m = re.search(r'Location\s*:\s*(.+)', self.req.http.header, re.I)
            if m:
                download_url = m.group(1)
                break
            elif "Entered figures don&#96;t coincide with the picture" in self.html:
                self.invalidCaptcha()
        else:
            self.fail(_("No valid captcha code entered"))

        self.req.http.c.setopt(FOLLOWLOCATION, 1)
        self.download(download_url)


    def checkErrors(self):
        if "All threads for IP" in self.html:
            self.logDebug("Your IP is already downloading a file")
            self.wait(5 * 60, True)
            self.retry()

        self.info.pop('error', None)


getInfo = create_getInfo(GigapetaCom)
