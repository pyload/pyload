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
    along with this program; if not, see <http://www.gnu.org/licenses/>
"""
from __future__ import absolute_import, unicode_literals

import re
import urllib.error
import urllib.parse
import urllib.request

from future import standard_library
standard_library.install_aliases()

from . import Crypter


class Dereferer(Crypter):
    __name__ = "Dereferer"
    __type__ = "crypter"
    __pattern__ = r'https?://([^/]+)/.*?(?P<url>(ht|f)tps?(://|%3A%2F%2F).*)'
    __version__ = "0.1"
    __description__ = """Crypter for dereferers"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    def decrypt(self, file):
        link = re.match(self.__pattern__, file.url).group('url')
        self.pyload.files.add_links(
            [urllib.parse.unquote(link).rstrip('+')], file.package().id)
