# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter
from module.common.json_layer import json_loads


class TurbobitNetFolder(SimpleCrypter):
    __name__    = "TurbobitNetFolder"
    __type__    = "crypter"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?turbobit\.net/download/folder/(?P<ID>\w+)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Turbobit.net folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'src=\'/js/lib/grid/icon/folder.png\'> <span>(.+?)</span>'


    def _getLinks(self, id, page=1):
        gridFile = self.load("http://turbobit.net/downloadfolder/gridFile",
                             get={"rootId": id, "rows": 200, "page": page}, decode=True)
        grid = json_loads(gridFile)

        if grid['rows']:
            for i in grid['rows']:
                yield i['id']
            for id in self._getLinks(id, page + 1):
                yield id
        else:
            return


    def getLinks(self):
        id = re.match(self.__pattern__, self.pyfile.url).group("ID")
        fixurl = lambda id: "http://turbobit.net/%s.html" % id
        return map(fixurl, self._getLinks(id))
