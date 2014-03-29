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
from urlparse import urljoin

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class MultiUpOrg(SimpleCrypter):
    __name__ = "MultiUpOrg"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?multiup\.org/(en|fr)/(?P<TYPE>project|download|miror)/\w+(/\w+)?"
    __version__ = "0.01"
    __description__ = """MultiUp.org crypter plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    TITLE_PATTERN = r'<title>.*(Project|Projet|ownload|élécharger) (?P<title>.+?) (\(|- )'

    def getLinks(self):
        m_type = re.match(self.__pattern__, self.pyfile.url).group("TYPE")

        if m_type == "project":
            pattern = r'\n(http://www\.multiup\.org/(?:en|fr)/download/.*)'
        else:
            pattern = r'style="width:97%;text-align:left".*\n.*href="(.*)"'
            if m_type == "download":
                dl_pattern = r'href="(.*)">.*\n.*<h5>DOWNLOAD</h5>'
                miror_page = urljoin("http://www.multiup.org", re.search(dl_pattern, self.html).group(1))
                self.html = self.load(miror_page)

        return re.findall(pattern, self.html)
