# -*- coding: utf-8 -*
#
# Test links:
#   https://drive.google.com/file/d/0B6RNTe4ygItBQm15RnJiTmMyckU/view?pli=1

import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.utils import html_unescape


class GoogledriveCom(SimpleHoster):
    __name__    = "GoogledriveCom"
    __type__    = "hoster"
    __version__ = "0.16"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(drive|docs)\.google\.com/(file/d/\w+|uc\?.*id=)'
    __config__  = [("activated"  , "bool", "Activated"                       , True),
                   ("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Drive.google.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'(?:<title>|class="uc-name-size".*>)(?P<N>.+?)(?: - Google Drive</title>|</a> \()'
    OFFLINE_PATTERN = r'align="center"><p class="errorMessage"'

    LINK_FREE_PATTERN = r'"([^"]+uc\?.*?)"'


    def setup(self):
        self.multiDL        = True
        self.resume_download = True
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        for _i in xrange(2):
            m = re.search(self.LINK_FREE_PATTERN, self.data)

            if m is None:
                return

            link = self.fixurl(link, "https://docs.google.com/")
            dl   = self.isdownload(link, redirect=False)

            if not dl:
                self.data = self.load(link)
            else:
                self.link = dl
                break


getInfo = create_getInfo(GoogledriveCom)
