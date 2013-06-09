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
"""

import re
import urllib

from module.plugins.Crypter import Crypter

class Dereferer(Crypter):
    __name__ = "Dereferer"
    __type__ = "crypter"
    __pattern__ = r'https?://([^/]+)/.*?(?P<url>(ht|f)tps?(://|%3A%2F%2F).*)'
    __version__ = "0.1"
    __description__ = """Crypter for dereferers"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    def decrypt(self, pyfile):
        link = re.match(self.__pattern__, self.pyfile.url).group('url')
        self.core.files.addLinks([ urllib.unquote(link).rstrip('+') ], self.pyfile.package().id)
