# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from pyload.plugin.internal.XFSHoster import XFSHoster


class UpleaCom(XFSHoster):
    __name__    = "UpleaCom"
    __type__    = "hoster"
    __version__ = "0.06"

    __pattern__ = r'https?://(?:www\.)?uplea\.com/dl/\w{15}'

    __description__ = """Uplea.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Redleon", "")]


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


    def handleFree(self, pyfile):
        m = re.search(self.STEP_PATTERN, self.html)
        if m is None:
            self.error(_("STEP_PATTERN not found"))

        self.html = self.load(urljoin("http://uplea.com/", m.group(1)))

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.wait(m.group(1), True)
            self.retry()

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_PATTERN not found"))

        self.link = m.group(1)
        self.wait(15)
