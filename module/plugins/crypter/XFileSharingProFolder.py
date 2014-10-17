# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSPCrypter import XFSPCrypter


class XFileSharingProFolder(XFSPCrypter):
    __name__ = "XFileSharingProFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'^unmatchable$'

    __description__ = """XFileSharingPro dummy folder decrypter plugin for hook"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    def setup(self):
        self.__pattern__ = self.core.pluginManager.crypterPlugins[self.__name__]['pattern']
        self.HOSTER_NAME = re.match(self.__pattern__, self.pyfile.url).group(1).lower()
