# -*- coding: utf-8 -*-
#
# Test links:
# http://d-h.st/mM8

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DevhostSt(SimpleHoster):
    __name__ = "DevhostSt"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?d-h\.st/(?!users/)\w{3}'

    __description__ = """d-h.st hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]


    FILE_NAME_PATTERN = r'>Filename:</span> <div title="(?P<N>.+?)"'
    FILE_SIZE_PATTERN = r'>Size:</span> (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>File Not Found<'
    LINK_PATTERN = r'id="downloadfile" href="(.+?)"'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1


    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error("Download link not found")

        dl_url = m.group(1)
        self.logDebug("Download URL = " + dl_url)
        self.download(dl_url, disposition=True)

        check = self.checkDownload({'html': re.compile("html")})
        if check == "html":
            self.error("Downloaded file is an html file")


getInfo = create_getInfo(DevhostSt)
