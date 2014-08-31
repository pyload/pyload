# -*- coding: utf-8 -*-

import math
import re
from urlparse import urljoin

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class TusfilesNetFolder(SimpleCrypter):
    __name__ = "TusfilesNetFolder"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/go/(?P<ID>\w+)/?'

    __description__ = """Tusfiles.net folder decrypter plugin"""
    __author_name__ = ("Walter Purcaro", "stickell")
    __author_mail__ = ("vuolter@gmail.com", "l.stickell@yahoo.it")

    LINK_PATTERN = r'<TD align=left><a href="(.*?)">'
    TITLE_PATTERN = r'<Title>.*?\: (?P<title>.+) folder</Title>'
    PAGES_PATTERN = r'>\((?P<pages>\d+) \w+\)<'

    URL_REPLACEMENTS = [(__pattern__, r'https://www.tusfiles.net/go/\g<ID>/')]


    def loadPage(self, page_n):
        return self.load(urljoin(self.pyfile.url, str(page_n)), decode=True)

    def handleMultiPages(self):
        pages = re.search(self.PAGES_PATTERN, self.html)
        if pages:
            pages = int(math.ceil(int(pages.group('pages')) / 25.0))
        else:
            return

        for p in xrange(2, pages + 1):
            self.html = self.loadPage(p)
            self.package_links += self.getLinks()
