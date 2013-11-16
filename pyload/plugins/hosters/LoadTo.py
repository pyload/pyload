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

    @author: halfman
"""

# Test links (random.bin):
# http://www.load.to/dNsmgXRk4/random.bin
# http://www.load.to/edbNTxcUb/random100.bin

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LoadTo(SimpleHoster):
    __name__ = "LoadTo"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?load\.to/\w+"
    __version__ = "0.12"
    __description__ = """Load.to hoster plugin"""
    __author_name__ = ("halfman", "stickell")
    __author_mail__ = ("Pulpan3@gmail.com", "l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'<a [^>]+>(?P<N>.+)</a></h3>\s*Size: (?P<S>\d+) Bytes'
    URL_PATTERN = r'<form method="post" action="(.+?)"'
    FILE_OFFLINE_PATTERN = r'Can\'t find file. Please check URL.<br />'
    WAIT_PATTERN = r'type="submit" value="Download \((\d+)\)"'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):

        self.html = self.load(pyfile.url, decode=True)

        found = re.search(self.URL_PATTERN, self.html)
        if not found:
            self.parseError('URL')
        download_url = found.group(1)

        timmy = re.search(self.WAIT_PATTERN, self.html)
        if timmy:
            self.setWait(timmy.group(1))
            self.wait()

        self.download(download_url, disposition=True)


getInfo = create_getInfo(LoadTo)
