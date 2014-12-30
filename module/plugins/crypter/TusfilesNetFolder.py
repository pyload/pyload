# -*- coding: utf-8 -*-

import math
import re
from urlparse import urljoin

from module.plugins.internal.XFSCrypter import XFSCrypter, create_getInfo


class TusfilesNetFolder(XFSCrypter):
    __name__    = "TusfilesNetFolder"
    __type__    = "crypter"
    __version__ = "0.08"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/go/(?P<ID>\w+)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Tusfiles.net folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "tusfiles.net"

    PAGES_PATTERN = r'>\((\d+) \w+\)<'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'https://www.tusfiles.net/go/\g<ID>/')]


    def loadPage(self, page_n):
        return self.load(urljoin(self.pyfile.url, str(page_n)), decode=True)


    def handlePages(self, pyfile):
        pages = re.search(self.PAGES_PATTERN, self.html)
        if pages:
            pages = int(math.ceil(int(pages.group('pages')) / 25.0))
        else:
            return

        for p in xrange(2, pages + 1):
            self.html = self.loadPage(p)
            self.links += self.getLinks()


getInfo = create_getInfo(TusfilesNetFolder)
