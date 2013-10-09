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

import math
import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter
from module.common.json_layer import json_loads


def format_links(fid):
    return 'http://turbobit.net/%s.html' % fid


class TurbobitNetFolder(SimpleCrypter):
    __name__ = "TurbobitNetFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:w{3}.)?turbobit\.net/download/folder/(?P<id>\w+)"
    __version__ = "0.01"
    __description__ = """Turbobit.net Folder Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    TITLE_PATTERN = r"<img src='/js/lib/grid/icon/folder.png'>(?P<title>.+)</div>"

    def getLinks(self):
        folder_id = re.search(self.__pattern__, self.pyfile.url).group('id')
        grid = self.load('http://turbobit.net/downloadfolder/gridFile',
                         get={'id_folder': folder_id, 'rows': 200}, decode=True)
        grid = json_loads(grid)

        links_count = grid["records"]
        pages = int(math.ceil(links_count / 200.0))

        ids = list()
        for i in grid['rows']:
            ids.append(i['id'])

        for p in range(2, pages + 1):
            grid = self.load('http://turbobit.net/downloadfolder/gridFile',
                             get={'id_folder': folder_id, 'rows': 200, 'page': p}, decode=True)
            grid = json_loads(grid)
            for i in grid['rows']:
                ids.append(i['id'])

        return map(format_links, ids)
