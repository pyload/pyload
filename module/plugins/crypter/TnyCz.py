#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: Walter Purcaro
###############################################################################

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class TnyCz(SimpleCrypter):
    __name__ = "TnyCz"
    __type__ = "crypter"
    __pattern__ = r'http://(?:www\.)?tny\.cz/\w+'
    __version__ = "0.01"
    __description__ = """Tny.cz plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    TITLE_PATTERN = r'<title>(?P<title>.+) - .+</title>'

    def getLinks(self):
        m = re.search(r'<a id=\'save_paste\' href="(.+save\.php\?hash=.+)">', self.html)
        return re.findall(".+", self.load(m.group(1), decode=True)) if m else None
