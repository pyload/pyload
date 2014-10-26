# -*- coding: utf-8 -*-
#
# Test links:
# http://remixshare.com/download/p946u
#
# Note:
# The remixshare.com website is very very slow, so
# if your download not starts because of pycurl timeouts:
# Adjust timeouts in /usr/share/pyload/module/network/HTTPRequest.py

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RemixshareCom(SimpleHoster):
    __name__ = "RemixshareCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://remixshare\.com/(download|dl)/\w+'

    __description__ = """Remixshare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de"),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_INFO_PATTERN = r'title=\'.+?\'>(?P<N>.+?)</span><span class=\'light2\'>&nbsp;\((?P<S>\d+)&nbsp;(?P<U>[\w^_]+)\)<'
    OFFLINE_PATTERN = r'<h1>Ooops!<'

    LINK_PATTERN = r'(http://remixshare\.com/downloadfinal/.+?)"'
    TOKEN_PATTERN = r'var acc = (\d+)'
    WAIT_PATTERN = r'var XYZ = r"(\d+)"'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1


    def handleFree(self):
        b = re.search(self.LINK_PATTERN, self.html)
        if not b:
            self.error(_("Cannot parse download url"))
        c = re.search(self.TOKEN_PATTERN, self.html)
        if not c:
            self.error(_("Cannot parse file token"))
        dl_url = b.group(1) + c.group(1)

        #Check if we have to wait
        seconds = re.search(self.WAIT_PATTERN, self.html)
        if seconds:
            self.logDebug("Wait " + seconds.group(1))
            self.wait(seconds.group(1))

        # Finally start downloading...
        self.download(dl_url, disposition=True)


getInfo = create_getInfo(RemixshareCom)
