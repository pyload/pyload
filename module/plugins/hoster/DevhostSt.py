# -*- coding: utf-8 -*-

#Testlink:
#http://d-h.st/mM8

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class DevhostSt(SimpleHoster):
    __name__ = "Devhost"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?d-h.st/\w+'
    __version__ = "0.01"
    __description__ = """d-h.st hoster plugin"""
    __author_name__ = ("zapp-brannigan")
    __author_mail__ = ("fuerst.reinje@web.de")

    FILE_NAME_PATTERN = r'div title=\"(?P<N>.+)\" style'
    FILE_SIZE_PATTERN = r'>Size:</span> (?P<S>.*) (?P<U>[kKmMgG]?i?[bB]) \(.*\)<'
    OFFLINE_PATTERN = r'>File Not Found<'
    LINK_PATTERN = r'id=\"downloadfile\" href=\"(.+)\">Download'

    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1 
           
    def handleFree(self):
        dl_url = re.search(self.LINK_PATTERN, self.html).group(1)
        self.logDebug("Download-URL = r" + dl_url)
        if not dl_url:
            self.parseError("Can not parse download url")
        self.download(dl_url, disposition=True)

getInfo = create_getInfo(DevhostSt)
