# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from pyload.utils import fixup


class NowDownloadEu(SimpleHoster):
    __name__ = "NowDownloadEu"
    __type__ = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?nowdownload\.(ch|co|eu|sx)/(dl/|download\.php\?id=)(?P<ID>\w+)'

    __description__ = """NowDownload.ch hoster plugin"""
    __author_name__ = ("godofdream", "Walter Purcaro")
    __author_mail__ = ("soilfiction@gmail.com", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'Downloading</span> <br> (?P<N>.*) (?P<S>[0-9,.]+) (?P<U>[kKMG])i?B </h4>'
    OFFLINE_PATTERN = r'(This file does not exist!)'

    TOKEN_PATTERN = r'"(/api/token\.php\?token=[a-z0-9]+)"'
    CONTINUE_PATTERN = r'"(/dl2/[a-z0-9]+/[a-z0-9]+)"'
    WAIT_PATTERN = r'\.countdown\(\{until: \+(\d+),'
    LINK_PATTERN = r'"(http://f\d+\.nowdownload\.ch/dl/[a-z0-9]+/[a-z0-9]+/[^<>"]*?)"'

    FILE_NAME_REPLACEMENTS = [("&#?\w+;", fixup), (r'<[^>]*>', '')]


    def setup(self):
        self.multiDL = self.resumeDownload = True
        self.chunkLimit = -1

    def handleFree(self):
        tokenlink = re.search(self.TOKEN_PATTERN, self.html)
        continuelink = re.search(self.CONTINUE_PATTERN, self.html)
        if tokenlink is None or continuelink is None:
            self.fail('Plugin out of Date')

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            wait = int(m.group(1))
        else:
            wait = 60

        baseurl = "http://www.nowdownload.ch"
        self.html = self.load(baseurl + str(tokenlink.group(1)))
        self.wait(wait)

        self.html = self.load(baseurl + str(continuelink.group(1)))

        url = re.search(self.LINK_PATTERN, self.html)
        if url is None:
            self.fail('Download Link not Found (Plugin out of Date?)')
        self.logDebug('Download link: ' + str(url.group(1)))
        self.download(str(url.group(1)))


getInfo = create_getInfo(NowDownloadEu)
