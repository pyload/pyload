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

    @author: Walter Purcaro
"""

from module.plugins.Crypter import Crypter

import re


class TnyCz(Crypter):
    __name__ = "TnyCz"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?tny\.cz/\w+"
    __version__ = "0.01"
    __description__ = """Tny.cz Plugin"""
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        m = re.search(r'<title>(.+)</title>', self.html)
        name = folder = m.group(1).rsplit(" - ")[0]

        m = re.search(r'<a id=\'save_paste\' href="(.+save\.php\?hash=.+)">', self.html)
        if m:
            links = re.findall(".+", self.load(m.group(1), decode=True))
            if links:
                self.packages = [(name, links, folder)]
                return
        self.fail('Could not extract any links')
