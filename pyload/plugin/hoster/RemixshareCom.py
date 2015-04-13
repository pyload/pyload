# -*- coding: utf-8 -*-
#
# Test links:
# http://remixshare.com/download/z8uli
#
# Note:
# The remixshare.com website is very very slow, so
# if your download not starts because of pycurl timeouts:
# Adjust timeouts in /usr/share/pyload/pyload/network/HTTPRequest.py

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class RemixshareCom(SimpleHoster):
    __name    = "RemixshareCom"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'https?://remixshare\.com/(download|dl)/\w+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Remixshare.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de"  ),
                       ("Walter Purcaro", "vuolter@gmail.com"     ),
                       ("sraedler"      , "simon.raedler@yahoo.de")]


    INFO_PATTERN    = r'title=\'.+?\'>(?P<N>.+?)</span><span class=\'light2\'>&nbsp;\((?P<S>\d+)&nbsp;(?P<U>[\w^_]+)\)<'
    HASHSUM_PATTERN = r'>(?P<T>MD5): (?P<H>\w+)'
    OFFLINE_PATTERN = r'<h1>Ooops!'

    LINK_PATTERN  = r'var uri = "(.+?)"'
    TOKEN_PATTERN = r'var acc = (\d+)'

    WAIT_PATTERN = r'var XYZ = "(\d+)"'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1


    def handleFree(self, pyfile):
        b = re.search(self.LINK_PATTERN, self.html)
        if not b:
            self.error(_("File url"))

        c = re.search(self.TOKEN_PATTERN, self.html)
        if not c:
            self.error(_("File token"))

        self.link = b.group(1) + "/zzz/" + c.group(1)

