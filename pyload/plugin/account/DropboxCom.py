# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class DropboxCom(SimpleHoster):
    __name    = "DropboxCom"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'https?://(?:www\.)?dropbox\.com/.+'

    __description = """Dropbox.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN = r'<title>Dropbox - (?P<N>.+?)<'
    SIZE_PATTERN = r'&nbsp;&middot;&nbsp; (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'<title>Dropbox - (404|Shared link error)<'

    COOKIES = [("dropbox.com", "lang", "en")]


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        self.resumeDownload = True


    def handleFree(self, pyfile):
        self.download(pyfile.url, get={'dl': "1"})
