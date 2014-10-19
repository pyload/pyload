# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DropboxCom(SimpleHoster):
    __name__ = "DropboxCom"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?dropbox\.com/.+'

    __description__ = """Dropbox.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]


    FILE_NAME_PATTERN = r'<title>Dropbox - (?P<N>.+?)<'
    FILE_SIZE_PATTERN = r'&nbsp;&middot;&nbsp; (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'<title>Dropbox - (404|Shared link error)<'

    COOKIES = [(".dropbox.com", "lang", "en")]


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        self.resumeDownload = True


    def handleFree(self):
        self.download(self.pyfile.url, get={'dl': "1"})

        check = self.checkDownload({'html': re.compile("html")})
        if check == "html":
            self.error("Downloaded file is an html file")


getInfo = create_getInfo(DropboxCom)
