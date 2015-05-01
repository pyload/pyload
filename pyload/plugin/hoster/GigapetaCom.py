# -*- coding: utf-8 -*-

import random
import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class GigapetaCom(SimpleHoster):
    __name    = "GigapetaCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?gigapeta\.com/dl/\w+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """GigaPeta.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<img src=".*" alt="file" />-->\s*(?P<N>.*?)\s*</td>'
    SIZE_PATTERN = r'<th>\s*Size\s*</th>\s*<td>\s*(?P<S>.*?)\s*</td>'
    OFFLINE_PATTERN = r'<div id="page_error">'

    COOKIES = [("gigapeta.com", "lang", "us")]


    def handleFree(self, pyfile):
        captcha_key = str(random.randint(1, 100000000))
        captcha_url = "http://gigapeta.com/img/captcha.gif?x=%s" % captcha_key

        for _i in xrange(5):
            self.checkErrors()

            captcha = self.decryptCaptcha(captcha_url)
            self.html = self.load(pyfile.url,
                                  post={'captcha_key': captcha_key,
                                        'captcha'    : captcha,
                                        'download'   : "Download"},
                                  follow_location=False)

            m = re.search(r'Location\s*:\s*(.+)', self.req.http.header, re.I)
            if m:
                self.link = m.group(1)
                break
            elif "Entered figures don&#96;t coincide with the picture" in self.html:
                self.invalidCaptcha()
        else:
            self.fail(_("No valid captcha code entered"))


    def checkErrors(self):
        if "All threads for IP" in self.html:
            self.logDebug("Your IP is already downloading a file")
            self.wait(5 * 60, True)
            self.retry()

        self.info.pop('error', None)
