# -*- coding: utf-8 -*-
#
# Test links:
# http://www.load.to/JWydcofUY6/random.bin
# http://www.load.to/oeSmrfkXE/random100.bin

import re

from ..captcha.SolveMedia import SolveMedia
from ..internal.SimpleHoster import SimpleHoster


class LoadTo(SimpleHoster):
    __name__ = "LoadTo"
    __type__ = "hoster"
    __version__ = "0.29"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?load\.to/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Load.to hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("halfman", "Pulpan3@gmail.com"),
                   ("stickell", "l.stickell@yahoo.it")]

    NAME_PATTERN = r'<h1>(?P<N>.+?)</h1>'
    SIZE_PATTERN = r'Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>Can\'t find file'

    LINK_FREE_PATTERN = r'<form method="post" action="(.+?)"'
    WAIT_PATTERN = r'type="submit" value="Download \((\d+)\)"'

    URL_REPLACEMENTS = [(r'(\w)$', r'\1/')]

    def setup(self):
        self.multiDL = True
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        #: Search for Download URL
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        self.link = m.group(1)

        #: Set Timer - may be obsolete
        m = re.search(self.WAIT_PATTERN, self.data)
        if m is not None:
            self.wait(m.group(1))

        #: Load.to is using SolveMedia captchas since ~july 2014:
        self.captcha = SolveMedia(pyfile)
        captcha_key = self.captcha.detect_key()

        if captcha_key:
            response, challenge = self.captcha.challenge(captcha_key)
            self.download(self.link,
                          post={'adcopy_challenge': challenge,
                                'adcopy_response': response,
                                'returnUrl': pyfile.url})
