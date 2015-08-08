# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class UpleaCom(XFSHoster):
    __name__    = "UpleaCom"
    __type__    = "hoster"
    __version__ = "0.12"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?uplea\.com/dl/\w{15}'

    __description__ = """Uplea.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Redleon", None),
                       ("GammaC0de", None)]


    HOSTER_DOMAIN = "uplea.com"

    SIZE_REPLACEMENTS = [('ko','KB'), ('mo','MB'), ('go','GB'), ('Ko','KB'), ('Mo','MB'), ('Go','GB')]

    NAME_PATTERN    = r'<span class="gold-text">(?P<N>.+?)</span>'
    SIZE_PATTERN    = r'<span class="label label-info agmd">(?P<S>[\d.,]+) (?P<U>[\w^_]+?)</span>'
    OFFLINE_PATTERN = r'>You followed an invalid or expired link'

    LINK_PATTERN = r'"(https?://\w+\.uplea\.com/anonym/.*?)"'

    PREMIUM_ONLY_PATTERN = r'You need to have a Premium subscription to download this file'
    WAIT_PATTERN         = r'timeText: ?([\d.]+),'
    STEP_PATTERN         = r'<a href="(/step/.+)">'


    def setup(self):
        self.multiDL = False
        self.chunk_limit = 1
        self.resume_download = True


    def handle_free(self, pyfile):
        m = re.search(self.STEP_PATTERN, self.html)
        if m is None:
            self.error(_("STEP_PATTERN not found"))

        self.html = self.load(urlparse.urljoin("http://uplea.com/", m.group(1)))

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.log_debug("Waiting %s seconds" % m.group(1))
            self.wait(m.group(1), True)
            self.retry()

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_PATTERN not found"))

        self.link = m.group(1)
        self.wait(15)


getInfo = create_getInfo(UpleaCom)
