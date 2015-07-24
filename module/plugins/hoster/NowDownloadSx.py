# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import fixup


class NowDownloadSx(SimpleHoster):
    __name__    = "NowDownloadSx"
    __type__    = "hoster"
    __version__ = "0.11"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(nowdownload\.[a-zA-Z]{2,}/(dl/|download\.php.+?id=|mobile/(#/files/|.+?id=))|likeupload\.org/)\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """NowDownload.sx hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("godofdream", "soilfiction@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN = r'Downloading</span> <br> (?P<N>.*) (?P<S>[\d.,]+) (?P<U>[\w^_]+) </h4>'
    OFFLINE_PATTERN = r'>This file does not exist'

    TOKEN_PATTERN = r'"(/api/token\.php\?token=\w+)"'
    CONTINUE_PATTERN = r'"(/dl2/\w+/\w+)"'
    WAIT_PATTERN = r'\.countdown\(\{until: \+(\d+),'
    LINK_FREE_PATTERN = r'(http://s\d+(?:\.coolcdn\.info|\.mighycdndelivery\.com)/nowdownload/.+?)["\']'

    NAME_REPLACEMENTS = [("&#?\w+;", fixup), (r'<.*?>', '')]


    def setup(self):
        self.resume_download = True
        self.multiDL        = True
        self.chunk_limit     = -1


    def handle_free(self, pyfile):
        tokenlink = re.search(self.TOKEN_PATTERN, self.html)
        continuelink = re.search(self.CONTINUE_PATTERN, self.html)
        if tokenlink is None or continuelink is None:
            self.error()

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            wait = int(m.group(1))
        else:
            wait = 60

        baseurl = "http://www.nowdownload.ch"
        self.html = self.load(baseurl + str(tokenlink.group(1)))
        self.wait(wait)

        self.html = self.load(baseurl + str(continuelink.group(1)))

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Download link not found"))

        self.link = m.group(1)


getInfo = create_getInfo(NowDownloadSx)
