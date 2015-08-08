# -*- coding: utf-8 -*-

import math
import re
import urlparse

from module.plugins.internal.XFSCrypter import XFSCrypter, create_getInfo


class TusfilesNetFolder(XFSCrypter):
    __name__    = "TusfilesNetFolder"
    __type__    = "crypter"
    __version__ = "0.09"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/go/(?P<ID>\w+)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Tusfiles.net folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    PAGES_PATTERN = r'>\((\d+) \w+\)<'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'https://www.tusfiles.net/go/\g<ID>/')]


    def load_page(self, page_n):
        return self.load(urlparse.urljoin(self.pyfile.url, str(page_n)))


    def handle_pages(self, pyfile):
        pages = re.search(self.PAGES_PATTERN, self.html)
        if pages:
            pages = int(math.ceil(int(pages.group('pages')) / 25.0))
        else:
            return

        for p in xrange(2, pages + 1):
            self.html = self.load_page(p)
            self.links += self.get_links()


getInfo = create_getInfo(TusfilesNetFolder)
