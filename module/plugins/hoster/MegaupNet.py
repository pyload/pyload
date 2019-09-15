# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster


class MegaupNet(SimpleHoster):
    __name__ = "MegaupNet"
    __type__ = "hoster"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r'https?://megaup.net/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Megaup.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'File: (?P<N>.+?)<'
    SIZE_PATTERN = r'Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'^unmatchable$'
    WAIT_PATTERN = r'var seconds = (\d+);'

    def handle_free(self, pyfile):
        m = re.search(r'\'(https://megaup\.net/\w+\?pt=.+?)\'', self.data)
        if m is not None:
            self.download(m.group(1), ref=pyfile.url)
