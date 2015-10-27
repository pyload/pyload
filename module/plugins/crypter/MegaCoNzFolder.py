# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Crypter import Crypter, create_getInfo


class MegaCoNzFolder(Crypter):
    __name__    = "MegaCoNzFolder"
    __type__    = "crypter"
    __version__ = "0.09"
    __status__  = "broken"

    __pattern__ = r'(https?://(?:www\.)?mega(\.co)?\.nz/|mega:|chrome:.+?)#F!(?P<ID>[\w^_]+)!(?P<KEY>[\w,\\-]+)'
    __config__  = [("activated"            , "bool", "Activated"                          , True),
                   ("use_premium"          , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Mega.co.nz folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def setup(self):
        self.req.setOption("timeout", 300)


    def decrypt(self, pyfile):
        url       = "https://mega.co.nz/#F!%s!%s" % re.match(self.__pattern__, pyfile.url).groups()
        self.data = self.load("http://rapidgen.org/linkfinder", post={'linklisturl': url})
        self.links = re.findall(r'(https://mega(\.co)?\.nz/#N!.+?)<', self.data)


getInfo = create_getInfo(MegaCoNzFolder)
