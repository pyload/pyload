# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
############################################################################

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class EasybytezComFolder(SimpleCrypter):
    __name__ = "EasybytezComFolder"
    __type__ = "crypter"
    __pattern__ = r"https?://(www\.)?easybytez\.com/users/\w+/\w+"
    __version__ = "0.01"
    __description__ = """Easybytez Crypter Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    LINK_PATTERN = r'<div class="link"><a href="(http://www\.easybytez\.com/\w+)" target="_blank">.+</a></div>'
    TITLE_PATTERN = r'<Title>Files of (?P<title>.+) folder</Title>'
    PAGES_PATTERN = r"<a href='[^']+'>(\d+)</a><a href='[^']+'>Next &#187;</a><br><small>\(\d+ total\)</small></div>"

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        package_name, folder_name = self.getPackageNameAndFolder()

        package_links = re.findall(self.LINK_PATTERN, self.html)

        pages = re.search(self.PAGES_PATTERN, self.html)
        if pages:
            pages = int(pages.group(1))
        else:
            pages = 1

        p = 2
        while p <= pages:
            self.html = self.load(pyfile.url, get={'page': p}, decode=True)
            package_links += re.findall(self.LINK_PATTERN, self.html)
            p += 1

        self.logDebug('Package has %d links' % len(package_links))

        if package_links:
            self.packages = [(package_name, package_links, folder_name)]
        else:
            self.fail('Could not extract any links')