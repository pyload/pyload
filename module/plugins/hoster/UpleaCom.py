# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class UpleaCom(XFSHoster):
    __name__    = "UpleaCom"
    __type__    = "hoster"
    __version__ = "0.10"

    __pattern__ = r'https?://(?:www\.)?uplea\.com/dl/\w{15}'

    __description__ = """Uplea.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Redleon", None),
                       ("GammaC0de", None)]


    DISPOSITION = False  #@TODO: Remove in 0.4.10

    NAME_PATTERN = r'<span class="gold-text">(?P<N>.+?)</span>'
    SIZE_PATTERN = r'<span class="label label-info agmd">(?P<S>[\d.,]+) (?P<U>[\w^_]+?)</span>'
    SIZE_REPLACEMENTS = [('ko','KB'), ('mo','MB'), ('go','GB'), ('Ko','KB'), ('Mo','MB'), ('Go','GB')]

    OFFLINE_PATTERN = r'>You followed an invalid or expired link'
    PREMIUM_PATTERN = r'You need to have a Premium subscription to download this file'

    LINK_PATTERN = r'"(https?://\w+\.uplea\.com/anonym/.*?)"'
    HOSTER_DOMAIN = "uplea.com"

    WAIT_PATTERN = r'timeText: ?([\d.]+),'
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
            self.logDebug(_("Waiting %s seconds") % m.group(1))
            self.wait(m.group(1), True)
            self.retry()

        m = re.search(self.PREMIUM_PATTERN, self.html)
        if m:
            self.error(_("This URL requires a premium account"))

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_PATTERN not found"))

        self.link = m.group(1)
        self.wait(15)


getInfo = create_getInfo(UpleaCom)
