# -*- coding: utf-8 -*-
#
# Test links:
# http://remixshare.com/download/z8uli
#
# Note:
# The remixshare.com website is very very slow, so
# if your download not starts because of pycurl timeouts:
# Adjust timeouts in /usr/share/pyload/module/network/HTTPRequest.py

import re

from ..internal.SimpleHoster import SimpleHoster


class RemixshareCom(SimpleHoster):
    __name__ = "RemixshareCom"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r'https?://remixshare\.com/(download|dl)/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Remixshare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("sraedler", "simon.raedler@yahoo.de")]

    INFO_PATTERN = r'title=\'.+?\'>(?P<N>.+?)</span><span class=\'light2\'>&nbsp;\((?P<S>\d+)&nbsp;(?P<U>[\w^_]+)\)<'
    HASHSUM_PATTERN = r'>(?P<H>MD5): (?P<D>\w+)'
    OFFLINE_PATTERN = r'<h1>Ooops!'

    LINK_PATTERN = r'var uri = "(.+?)"'
    TOKEN_PATTERN = r'var acc = (\d+)'

    WAIT_PATTERN = r'var XYZ = "(\d+)"'

    def setup(self):
        self.multiDL = True
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        b = re.search(self.LINK_PATTERN, self.data)
        if not b:
            self.error(_("File url"))

        c = re.search(self.TOKEN_PATTERN, self.data)
        if not c:
            self.error(_("File token"))

        self.link = b.group(1) + "/zzz/" + c.group(1)
