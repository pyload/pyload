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
    __config__  = [("activated", "bool", "Activated", True),
                   ("use_premium", "bool", "Use premium account if available", True)]

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

        self.check_errors()

        captcha = self.captcha.decrypt(captcha_url)
        header  = self.load(pyfile.url,
                            post={'captcha_key': captcha_key,
                                  'captcha'    : captcha,
                                  'download'   : "Download"},
                            just_header=True)

        self.link = header.get('location')


getInfo = create_getInfo(GigapetaCom)
