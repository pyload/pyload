# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class NitroflareComFolder(SimpleCrypter):
    __name__    = "NitroflareComFolder"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?nitroflare\.com/folder/(?P<USER>\d+)/(?P<ID>[\w=]+)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Nitroflare.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def getLinks(self):
        res = json_loads(self.load("http://nitroflare.com/ajax/folder.php",
                                   post={'userId' : self.info['pattern']['USER'],
                                         'folder' : self.info['pattern']['ID'],
                                         'page'   : 1,
                                         'perPage': 10000},
                                   decode=True))
        if res['name']:
            self.pyfile.name = res['name']
        else:
            self.offline()

        return [link['url'] for link in res['files']] if 'files' in res else None


getInfo = create_getInfo(NitroflareComFolder)
