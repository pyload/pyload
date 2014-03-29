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
###############################################################################

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter
from module.common.json_layer import json_loads


class TurbobitNetFolder(SimpleCrypter):
    __name__ = "TurbobitNetFolder"
    __type__ = "crypter"
    __pattern__ = r'http://(?:www\.)?turbobit\.net/download/folder/(?P<ID>\w+)'
    __version__ = "0.03"
    __description__ = """Turbobit.net folder decrypter plugin"""
    __author_name__ = ("stickell", "Walter Purcaro")
    __author_mail__ = ("l.stickell@yahoo.it", "vuolter@gmail.com")

    TITLE_PATTERN = r"src='/js/lib/grid/icon/folder.png'> <span>(?P<title>.+?)</span>"

    def _getLinks(self, id, page=1):
        gridFile = self.load("http://turbobit.net/downloadfolder/gridFile",
                             get={"rootId": id, "rows": 200, "page": page}, decode=True)
        grid = json_loads(gridFile)

        if grid["rows"]:
            for i in grid["rows"]:
                yield i["id"]
            for id in self._getLinks(id, page + 1):
                yield id
        else:
            return

    def getLinks(self):
        id = re.match(self.__pattern__, self.pyfile.url).group("ID")
        fixurl = lambda id: "http://turbobit.net/%s.html" % id
        return map(fixurl, self._getLinks(id))
