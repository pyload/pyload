# -*- coding: utf-8 -*-
#
# Test links:
# http://d-h.st/mM8

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class DevhostSt(SimpleHoster):
    __name    = "DevhostSt"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?d-h\.st/(?!users/)\w{3}'

    __description = """d-h.st hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN = r'>Filename:</span> <div title="(?P<N>.+?)"'
    SIZE_PATTERN = r'>Size:</span> (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>File Not Found<'
    LINK_PATTERN = r'id="downloadfile" href="(.+?)"'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1


    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("Download link not found"))

        dl_url = m.group(1)
        self.download(dl_url, disposition=True)

        check = self.checkDownload({'html': re.compile("html")})
        if check == "html":
            self.error(_("Downloaded file is an html page"))


getInfo = create_getInfo(DevhostSt)
