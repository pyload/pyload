# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import fixup


class NowDownloadEu(SimpleHoster):
    __name__    = "NowDownloadEu"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?nowdownload\.(at|ch|co|eu|sx)/(dl/|download\.php\?id=)\w+'

    __description__ = """NowDownload.at hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("godofdream", "soilfiction@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_INFO_PATTERN = r'Downloading</span> <br> (?P<N>.*) (?P<S>[\d.,]+) (?P<U>[\w^_]+) </h4>'
    OFFLINE_PATTERN = r'>This file does not exist'

    TOKEN_PATTERN = r'"(/api/token\.php\?token=\w+)"'
    CONTINUE_PATTERN = r'"(/dl2/\w+/\w+)"'
    WAIT_PATTERN = r'\.countdown\(\{until: \+(\d+),'
    LINK_PATTERN = r'"(http://f\d+\.nowdownload\.at/dl/\w+/\w+)'

    FILE_NAME_REPLACEMENTS = [("&#?\w+;", fixup), (r'<[^>]*>', '')]


    def setup(self):
        self.multiDL = self.resumeDownload = True
        self.chunkLimit = -1


    def handleFree(self):
        tokenlink = re.search(self.TOKEN_PATTERN, self.html)
        continuelink = re.search(self.CONTINUE_PATTERN, self.html)
        if tokenlink is None or continuelink is None:
            self.error()

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            wait = int(m.group(1))
        else:
            wait = 60

        baseurl = "http://www.nowdownload.at"
        self.html = self.load(baseurl + str(tokenlink.group(1)))
        self.wait(wait)

        self.html = self.load(baseurl + str(continuelink.group(1)))

        url = re.search(self.LINK_PATTERN, self.html)
        if url is None:
            self.error(_("Download link not found"))

        self.download(str(url.group(1)))


getInfo = create_getInfo(NowDownloadEu)
