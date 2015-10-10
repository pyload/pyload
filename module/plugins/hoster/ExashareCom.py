# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class ExashareCom(XFSHoster):
    __name__    = "ExashareCom"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?exashare\.com/\w{12}'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Exashare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN      = r'>(?P<NAME>.+?)<small>\( (?P<S>[\d.,]+) (?P<U>[\w^_]+)'


    def setup(self):
        self.multiDL        = True
        self.chunk_limit     = 1
        self.resume_download = self.premium


    def handle_free(self, pyfile):
        return super(XFSHoster, self).handle_free(pyfile)


getInfo = create_getInfo(ExashareCom)
