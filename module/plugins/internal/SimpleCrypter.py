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

from re import findall
from module.plugins.Crypter import Crypter

class SimpleCrypter(Crypter):
    __name__ = "SimpleCrypter"
    __version__ = "0.01"
    __pattern__ = None
    __type__ = "crypter"
    __description__ = """Base crypter plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    def init(self):
        self.url = self.pyfile.url
    
    def decrypt(self, pyfile):
        self.html = self.load(self.url)

        new_links = []
        new_links.extend(findall(self.LINK_PATTERN, self.html))

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')