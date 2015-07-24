# -*- coding: utf-8 -*-

import pycurl
import random
import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class GigapetaCom(SimpleHoster):
    __name__    = "GigapetaCom"
    __type__    = "hoster"
    __version__ = "0.05"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?gigapeta\.com/dl/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """GigaPeta.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'<img src=".*" alt="file" />-->\s*(?P<N>.*?)\s*</td>'
    SIZE_PATTERN    = r'<th>\s*Size\s*</th>\s*<td>\s*(?P<S>.*?)\s*</td>'
    OFFLINE_PATTERN = r'<div id="page_error">'

    DOWNLOAD_PATTERN = r'"All threads for IP'

    COOKIES = [("gigapeta.com", "lang", "us")]


    def handle_free(self, pyfile):
        captcha_key = str(random.randint(1, 100000000))
        captcha_url = "http://gigapeta.com/img/captcha.gif?x=%s" % captcha_key

        self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 0)

        for _i in xrange(5):
            self.check_errors()

            captcha = self.captcha.decrypt(captcha_url)
            self.html = self.load(pyfile.url, post={
                'captcha_key': captcha_key,
                'captcha': captcha,
                'download': "Download"})

            m = re.search(r'Location\s*:\s*(.+)', self.req.http.header, re.I)
            if m:
                self.link = m.group(1).rstrip()  #@TODO: Remove .rstrip() in 0.4.10
                break
            elif "Entered figures don&#96;t coincide with the picture" in self.html:
                self.captcha.invalid()
        else:
            self.fail(_("No valid captcha code entered"))

        self.req.http.c.setopt(pycurl.FOLLOWLOCATION, 1)


getInfo = create_getInfo(GigapetaCom)
