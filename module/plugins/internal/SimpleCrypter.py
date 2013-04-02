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

class SimpleCrypter(Crypter):
    __name__ = "SimpleCrypter"
    __version__ = "0.04"
    __pattern__ = None
    __type__ = "crypter"
    __description__ = """Base crypter plugin"""
    __author_name__ = ("stickell", "zoidberg")
    __author_mail__ = ("l.stickell@yahoo.it", "zoidberg@mujmail.cz")
    """
    These patterns should be defined by each hoster:

    LINK_PATTERN: group(1) must be a download link
    example: <div class="link"><a href="(http://speedload.org/\w+)

    TITLE_PATTERN: (optional) the group defined by 'title' should be the title
    example: <title>Files of: (?P<title>[^<]+) folder</title>
    """

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        package_name, folder_name = self.getPackageNameAndFolder()

        package_links = re.findall(self.LINK_PATTERN, self.html)
        self.logDebug('Package has %d links' % len(package_links))

        if package_links:
            self.packages = [(package_name, package_links, folder_name)]
        else:
            self.fail('Could not extract any links')

    def getPackageNameAndFolder(self):
        if hasattr(self, 'TITLE_PATTERN'):
            m = re.search(self.TITLE_PATTERN, self.html)
            if m:
                name = folder = m.group('title')
                self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
                return name, folder

        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
        return name, folder
