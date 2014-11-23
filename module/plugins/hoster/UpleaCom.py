# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class UpleaCom(XFSHoster):
    __name__    = "UpleaCom"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'https?://(?:www\.)?uplea\.com/dl/\w{15}'

    __description__ = """Uplea.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Redleon", None)]


    HOSTER_DOMAIN = "uplea.com"

    NAME_PATTERN = r'class="agmd size18">(?P<N>.+?)<'
    SIZE_PATTERN = r'size14">(?P<S>[\d.,]+) (?P<U>[\w^_])</span>'

    OFFLINE_PATTERN = r'>You followed an invalid or expired link'

    LINK_PATTERN = r'"(http?://\w+\.uplea\.com/anonym/.*?)"'
    WAIT_PATTERN = r'timeText:([\d.]+),'
    STEP_PATTERN = r'<a href="(/step/.+)">'


    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1
        self.resumeDownload = True


    def handleFree(self):
        m = re.search(self.STEP_PATTERN, self.html)
        if m is None:
            self.error("STEP_PATTERN not found")

        self.html = self.load(urljoin("http://uplea.com/", m.group(1)))

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
