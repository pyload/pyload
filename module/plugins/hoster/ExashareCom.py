# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class ExashareCom(XFSHoster):
    __name__    = "ExashareCom"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?exashare\.com/\w{12}'

    __description__ = """Exashare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN      = r'>(?P<NAME>.+?)<small>\( (?P<S>[\d.,]+) (?P<U>[\w^_]+)'


    def setup(self):
        self.multiDL        = True
        self.chunk_limit     = 1
        self.resume_download = self.premium


    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))
        else:
            self.link = m.group(1)


getInfo = create_getInfo(ExashareCom)
