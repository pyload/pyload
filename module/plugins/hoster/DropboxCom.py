# -*- coding: utf-8 -*-
# Testlink: https://www.dropbox.com/s/0ht5e3wuoh33dx4/CMKeyguard.apk

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class DropboxCom(SimpleHoster):
    __name__ = "DropboxCom"
    __type__ = "hoster"
    __pattern__ = r'https?://(www\.)?dropbox.com/.+'
    __version__ = "0.01"
    __description__ = """DropboxCom hoster plugin"""
    __author_name__ = ("zapp-brannigan")
    __author_mail__ = ("fuerst.reinje@web.de")

    FILE_NAME_PATTERN = r'<title>Dropbox - (?P<N>.+)</title>'
    FILE_SIZE_PATTERN = r'class="meta">.*&nbsp;&middot;&nbsp; (?P<S>.+) (?P<U>[kKmMgG]?i?[bB]?[yte]?)</div>'
    OFFLINE_PATTERN = r'(<title>Dropbox - 404</title>|<title>Dropbox - Shared link error</title>)'
    SH_COOKIES = [ (".dropbox.com", "lang", "en") ]

    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        
    def process(self,pyfile):
        self.download(pyfile.url, get={ "dl": "1"})
        check = self.checkDownload({"is_html": re.compile("html")})
        if check == "is_html":
            self.fail("The downloaded file is html, something went wrong. Maybe the plugin is out of date")
        
getInfo = create_getInfo(DropboxCom)
