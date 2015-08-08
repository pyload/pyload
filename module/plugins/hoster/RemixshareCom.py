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

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RemixshareCom(SimpleHoster):
    __name__    = "RemixshareCom"
    __type__    = "hoster"
    __version__ = "0.06"
    __status__  = "testing"

    __pattern__ = r'https?://remixshare\.com/(download|dl)/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Remixshare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de"  ),
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
        self.chunk_limit = 1


    def handle_free(self, pyfile):
        b = re.search(self.LINK_PATTERN, self.html)
        if not b:
            self.error(_("File url"))

        c = re.search(self.TOKEN_PATTERN, self.html)
        if not c:
            self.error(_("File token"))

        self.link = b.group(1) + "/zzz/" + c.group(1)


getInfo = create_getInfo(RemixshareCom)
