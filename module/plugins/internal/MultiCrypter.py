# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class MultiCrypter(SimpleCrypter):
    __name__    = "MultiCrypter"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Multi decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def init(self):
        self.CRYPTER_NAME = self.pyload.pluginManager.crypterPlugins[self.__name__]['name']


    def _log(self, level, plugintype, pluginname, messages):
        return super(MultiCrypter, self)._log(level,
                                              plugintype,
                                              pluginname,
                                              (self.CRYPTER_NAME,) + messages)
