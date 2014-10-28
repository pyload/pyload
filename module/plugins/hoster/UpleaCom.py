# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class UpleaCom(XFSPHoster):
    __name__    = "UpleaCom"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?uplea\.com/dl/\w{15}'

    __description__ = """Uplea.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Redleon", None)]


    HOSTER_NAME = "uplea.com"

    FILE_INFO_PATTERN = r'class="l download-filename">\s<span.*?>(?P<N>.+)</span>\s<span.*?>(?P<S>[\d.]+) (?P<U>[\w]).*?</span>'
    OFFLINE_PATTERN = r'You followed an invalid or expired link'

    LINK_PATTERN = r'"(http?://\w+\.uplea\.com/anonym/.*?)"'
    WAIT_PATTERN = r'timeText:([\d.]+),'
    VARS_PATTERN = r'class="cel_tbl_step1_foot">\s<a href="(/step/.+)">'


    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1
        self.resumeDownload = True


    def handleFree(self):
        m = re.search(self.VARS_PATTERN, self.html)
        if m is None:
            self.error("VARS_PATTERN not found")

        self.html = self.load('http://uplea.com%s' % m.groups(1))

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.wait(m.group(1), True)
            self.retry()

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error("LINK_PATTERN not found")

        self.wait(15)
        self.download(m.group(1), disposition=True)


getInfo = create_getInfo(UpleaCom)
