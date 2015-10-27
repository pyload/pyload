# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo
from module.plugins.internal.utils import json


class TurbobitNetFolder(SimpleCrypter):
    __name__    = "TurbobitNetFolder"
    __type__    = "crypter"
    __version__ = "0.09"
    __status__  = "broken"

    __pattern__ = r'http://(?:www\.)?turbobit\.net/download/folder/(?P<ID>\w+)'
    __config__  = [("activated"            , "bool", "Activated"                                        , True),
                   ("use_premium"          , "bool", "Use premium account if available"                 , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"                        , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package"              , True),
                   ("max_wait"             , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Turbobit.net folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'src=\'/js/lib/grid/icon/folder.png\'> <span>(?P<N>.+?)</span>'


    def _get_links(self, id, page=1):
        gridFile = self.load("http://turbobit.net/downloadfolder/gridFile",
                             get={'rootId': id, 'rows': 200, 'page': page})
        grid = json.loads(gridFile)

        if grid['rows']:
            for i in grid['rows']:
                yield i['id']
            for id in self._get_links(id, page + 1):
                yield id
        else:
            return


    def get_links(self):
        return ["http://turbobit.net/%s.html" % id for id in self._get_links(self.info['pattern']['ID'])]


getInfo = create_getInfo(TurbobitNetFolder)
