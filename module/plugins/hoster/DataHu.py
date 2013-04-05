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

# Test links (random.bin):
# http://data.hu/get/6381232/random.bin

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DataHu(SimpleHoster):
    __name__ = "DataHu"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?data.hu/get/\w+"
    __version__ = "0.01"
    __description__ = """Data.hu Download Hoster"""
    __author_name__ = ("crash", "stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_INFO_PATTERN = ur'<title>(?P<N>.*) \((?P<S>[^)]+)\) let\xf6lt\xe9se</title>'
    FILE_OFFLINE_PATTERN = ur'Az adott f\xe1jl nem l\xe9tezik'
    DIRECT_LINK_PATTERN = r'<div class="download_box_button"><a href="([^"]+)">'

    def handleFree(self):
        self.resumeDownload = True
        self.html = self.load(self.pyfile.url, decode=True)

        m = re.search(self.DIRECT_LINK_PATTERN, self.html)
        if m:
            url = m.group(1)
            self.logDebug('Direct link: ' + url)
        else:
            self.parseError('Unable to get direct link')

        self.download(url, disposition=True)


getInfo = create_getInfo(DataHu)
