# -*- coding: utf-8 -*
#
# Test links:
#   https://drive.google.com/file/d/0B6RNTe4ygItBQm15RnJiTmMyckU/view?pli=1

import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.plugins.internal.misc import html_unescape


class GoogledriveCom(SimpleHoster):
    __name__    = "GoogledriveCom"
    __type__    = "hoster"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(drive|docs)\.google\.com/(file/d/\w+|uc\?.*id=)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Drive.google.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'(?:<title>|class="uc-name-size".*>)(?P<N>.+?)(?: - Google Drive</title>|</a> \()'
    OFFLINE_PATTERN = r'align="center"><p class="errorMessage"'


    def setup(self):
        self.multiDL         = True
        self.resume_download = True
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        for _i in xrange(2):
            m = re.search(r'"([^"]+uc\?.*?)"', self.data)

            if m is None:
                return

            link = self.fixurl(m.group(1), "https://docs.google.com/")

            if re.search(r'/uc\?.*&confirm=', link):
                self.link = link
                return
            else:
                self.data = self.load(link)
