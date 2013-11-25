# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

import re

from module.plugins.Crypter import Crypter
from module.utils import html_unescape
from module.plugins.internal.SimpleHoster import replace_patterns


class SimpleCrypter(Crypter):
    __name__ = "SimpleCrypter"
    __version__ = "0.07"
    __pattern__ = None
    __type__ = "crypter"
    __description__ = """Base crypter plugin"""
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

    loadPage(self, page_n):
    must return the html of the page number 'page_n'
    """

    FILE_URL_REPLACEMENTS = []

    def decrypt(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.FILE_URL_REPLACEMENTS)

        self.html = self.load(pyfile.url, decode=True)

        package_name, folder_name = self.getPackageNameAndFolder()

        self.package_links = self.getLinks()

        if hasattr(self, 'PAGES_PATTERN') and hasattr(self, 'loadPage'):
            self.handleMultiPages()

        self.logDebug('Package has %d links' % len(self.package_links))

        if self.package_links:
            self.packages = [(package_name, self.package_links, folder_name)]
        else:
            self.fail('Could not extract any links')

    def getLinks(self):
        """
        Returns the links extracted from self.html
        You should override this only if it's impossible to extract links using only the LINK_PATTERN.
        """
        return re.findall(self.LINK_PATTERN, self.html)

    def getPackageNameAndFolder(self):
        if hasattr(self, 'TITLE_PATTERN'):
            m = re.search(self.TITLE_PATTERN, self.html)
            if m:
                name = folder = html_unescape(m.group('title').strip())
                self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
                return name, folder

        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
        return name, folder

    def handleMultiPages(self):
        pages = re.search(self.PAGES_PATTERN, self.html)
        if pages:
            pages = int(pages.group('pages'))
        else:
            pages = 1

        for p in range(2, pages + 1):
            self.html = self.loadPage(p)
            self.package_links += self.getLinks()
