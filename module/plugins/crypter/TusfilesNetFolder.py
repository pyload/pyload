# -*- coding: utf-8 -*-

import math
import re
import urlparse

from module.plugins.internal.XFSCrypter import XFSCrypter


class TusfilesNetFolder(XFSCrypter):
    __name__    = "TusfilesNetFolder"
    __type__    = "crypter"
    __version__ = "0.16"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/go/(?P<ID>\w+)'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

    __description__ = """Tusfiles.net folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    PLUGIN_DOMAIN = "tusfiles.net"
    PAGES_PATTERN = r'>\((\d+) \w+\)<'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'https://www.tusfiles.net/go/\g<ID>/')]


    def load_page(self, page_n):
        return self.load(urlparse.urljoin(self.pyfile.url, str(page_n)))


    def handle_pages(self, pyfile):
        pages = re.search(self.PAGES_PATTERN, self.data)

        if pages:
            pages = int(math.ceil(int(pages.group('pages')) / 25.0))
        else:
            return

        links = self.links
        for p in xrange(2, pages + 1):
            self.data = self.load_page(p)
            links.append(self.get_links())

        self.links = links
