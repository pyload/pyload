# -*- coding: utf-8 -*-
#Testlink:
#http://remixshare.com/download/p946u
#
# The remixshare.com website is very very slow, so
# if your download not starts because of pycurl timeouts:
# Adjust timeouts in /usr/share/pyload/module/network/HTTPRequest.py
#

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RemixshareCom(SimpleHoster):
    __name__ = "RemixshareCom"
    __type__ = "hoster"
    __pattern__ = r'https?://remixshare\.com/(download|dl)/\w+'
    __version__ = "0.01"
    __description__ = """Remixshare.com hoster plugin"""
    __author_name__ = ("zapp-brannigan", "Walter Purcaro")
    __author_mail__ = ("fuerst.reinje@web.de", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'title=\'.+?\'>(?P<N>.+?)</span><span class=\'light2\'>&nbsp;\((?P<S>\d+)&nbsp;(?P<U>\w+)\)<'
    OFFLINE_PATTERN = r'<h1>Ooops!<'

    WAIT_PATTERN = r'var XYZ = "(\d+)"'
    FILE_URL_PATTERN = r'(http://remixshare.com/downloadfinal/.+?)"'
    FILE_TOKEN_PATTERN = r'var acc = (\d+)'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1

    def handleFree(self):
        b = re.search(self.FILE_URL_PATTERN, self.html)
        if not b:
            self.fail("Can not parse download url")
        c = re.search(self.FILE_TOKEN_PATTERN, self.html)
        if not c:
            self.fail("Can not parse file token")
        dl_url = b.group(1) + c.group(1)

        #Check if we have to wait
        seconds = re.search(self.WAIT_PATTERN, self.html)
        if seconds:
            self.logDebug("Wait " + seconds.group(1))
            self.wait(seconds.group(1))

        # Finally start downloading...
        self.logDebug("Download-URL: " + dl_url)
        self.download(dl_url, disposition=True)


getInfo = create_getInfo(RemixshareCom)
