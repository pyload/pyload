# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DropboxCom(SimpleHoster):
    __name__    = "DropboxCom"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'https?://(?:www\.)?dropbox\.com/.+'

    __description__ = """Dropbox.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


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


getInfo = create_getInfo(DropboxCom)
