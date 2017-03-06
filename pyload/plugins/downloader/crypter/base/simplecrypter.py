# -*- coding: utf-8 -*-
# @author: zoidberg

from __future__ import absolute_import, division, unicode_literals

import re
from builtins import int, range

from future import standard_library

from pyload.plugins.hoster.base.simplehoster import replace_patterns
from pyload.utils.web import purge as webpurge

from .. import Crypter, Package

standard_library.install_aliases()


class SimpleCrypter(Crypter):
    __name__ = "SimpleCrypter"
    __version__ = "0.07"
    __pattern__ = None
    __type__ = "crypter"
    __description__ = """Simple decrypter plugin"""
    __author_name__ = ("stickell", "zoidberg")
    __author_mail__ = ("l.stickell@yahoo.it", "zoidberg@mujmail.cz")
    """
    These patterns should be defined by each crypter:

    LINK_PATTERN: group(1) must be a download link
    example: <div class="link"><a href="(http://speedload.org/\w+)

    TITLE_PATTERN: (optional) the group defined by 'title' should be the title
    example: <title>Files of: (?P<title>[^<]+) folder</title>

    If it's impossible to extract the links using the LINK_PATTERN only you can override the getLinks method.

    If the links are disposed on multiple pages you need to define a pattern:

    PAGES_PATTERN: the group defined by 'pages' must be the total number of pages

    and a function:

    load_page(self, page_n):
    must return the html of the page number 'page_n'
    """
    FILE_URL_REPLACEMENTS = []

    def decrypt_url(self, url):
        url = replace_patterns(url, self.FILE_URL_REPLACEMENTS)

        self.html = self.load(url, decode=True)

        package_name = self.get_package_name()
        self.package_links = self.get_links()

        if hasattr(self, 'PAGES_PATTERN') and hasattr(self, 'loadPage'):
            self.handle_multi_pages()

        self.log_debug('Package has {0:d} links'.format(
            len(self.package_links)))

        if self.package_links:
            return Package(package_name, self.package_links)
        else:
            self.fail(_('Could not extract any links'))

    def get_links(self):
        """
        Returns the links extracted from self.html
        You should override this only if it's impossible to extract links using only the LINK_PATTERN
        """
        return re.findall(self.LINK_PATTERN, self.html)

    def get_package_name(self):
        if hasattr(self, 'TITLE_PATTERN'):
            m = re.search(self.TITLE_PATTERN, self.html)
            if m:
                name = webpurge.escape(m.group('title').strip())
                self.log_debug("Found name [{0}] in package info".format(name))
                return name

        return None

    def handle_multi_pages(self):
        pages = re.search(self.PAGES_PATTERN, self.html)
        if pages:
            pages = int(pages.group('pages'))
        else:
            pages = 1

        for p in range(2, pages + 1):
            self.html = self.load_page(p)
            self.package_links += self.get_links()
