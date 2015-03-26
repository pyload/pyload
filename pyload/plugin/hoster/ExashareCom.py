# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.XFSHoster import XFSHoster


class ExashareCom(XFSHoster):
    __name    = "ExashareCom"
    __type    = "hoster"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?exashare\.com/\w{12}'

    __description = """Exashare.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN      = r'>(?P<NAME>.+?)<small>\( (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    LINK_FREE_PATTERN = r'file: "(.+?)"'


    def setup(self):
        self.multiDL        = True
        self.chunkLimit     = 1
        self.resumeDownload = self.premium


    def handleFree(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))
        else:
            self.link = m.group(1)
