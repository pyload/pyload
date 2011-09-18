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
from module.plugins.Hoster import Hoster

class PrzeklejPl(Hoster):
    __name__ = "PrzeklejPl"
    __type__ = "hoster"
    __pattern__ = r"http://.*przeklej.pl/plik/.*"
    __version__ = "0.1"
    __description__ = """przeklej.pl"""
    __author_name__ = ("zoidberg")

    FILE_URL_PATTERN = r'<a href="([^"]+)" title="Pobierz plik">([^<]+)</a>'

    #ERR_PATTERN = r'<p class="errorreport_error">Chyba: ([^<]+)</p>'

    def setup(self):
        self.multiDL = True

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        found = re.search(self.FILE_URL_PATTERN, self.html)
        if found is None:
            self.fail("Parse error (URL)")
        parsed_url = found.group(1)
        pyfile.name = found.group(2)

        self.download("http://www.przeklej.pl" + parsed_url)
        