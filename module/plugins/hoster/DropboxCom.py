# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DropboxCom(SimpleHoster):
    __name__    = "DropboxCom"
    __type__    = "hoster"
    __version__ = "0.05"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?dropbox\.com/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Dropbox.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN = r'<title>Dropbox - (?P<N>.+?)<'
    SIZE_PATTERN = r'&nbsp;&middot;&nbsp; (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'<title>Dropbox - (404|Shared link error)<'

    COOKIES = [("dropbox.com", "lang", "en")]


    def setup(self):
        self.multiDL        = True
        self.chunk_limit     = 1
        self.resume_download = True


    def handle_free(self, pyfile):
        self.download(pyfile.url, get={'dl': "1"})


getInfo = create_getInfo(DropboxCom)
