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
        dl_url = re.search(self.LINK_PATTERN, self.html)
        if dl_url is None:
            self.fail("Can not find download url. Maybe the plugin is out of date")
        self.logDebug("Download-URL = " + dl_url.group(1))
        self.download(dl_url.group(1), disposition=True)
        check = self.checkDownload({"is_html": re.compile("html")})
        if check == "is_html":
            self.fail("The downloaded file is html, something went wrong. Maybe the plugin is out of date")

getInfo = create_getInfo(DevhostSt)
