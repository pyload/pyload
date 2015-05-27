# -*- coding: utf-8 -*
#
# Test links:
#   https://drive.google.com/file/d/0B6RNTe4ygItBQm15RnJiTmMyckU/view?pli=1

import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import html_unescape


class GoogledriveCom(SimpleHoster):
    __name__    = "GoogledriveCom"
    __type__    = "hoster"
    __version__ = "0.12"

    __pattern__ = r'https?://(?:www\.)?(drive|docs)\.google\.com/(file/d/\w+|uc\?.*id=)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Drive.google.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    DISPOSITION = False  #: Remove in 0.4.10

    NAME_PATTERN    = r'(?:<title>|class="uc-name-size".*>)(?P<N>.+?)(?: - Google Drive</title>|</a> \()'
    OFFLINE_PATTERN = r'align="center"><p class="errorMessage"'

    LINK_FREE_PATTERN = r'"([^"]+uc\?.*?)"'


    def setup(self):
        self.multiDL        = True
        self.resumeDownload = True
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        for _i in xrange(2):
            m = re.search(self.LINK_FREE_PATTERN, self.html)

            if m is None:
                self.error(_("Free download link not found"))

            else:
                link = html_unescape(m.group(1).decode('unicode-escape'))
                if not urlparse.urlparse(link).scheme:
                    link = urlparse.urljoin("https://docs.google.com/", link)

                direct_link = self.directLink(link, False)
                if not direct_link:
                    self.html = self.load(link, decode=True)
                else:
                    self.link = direct_link
                    break


getInfo = create_getInfo(GoogledriveCom)
