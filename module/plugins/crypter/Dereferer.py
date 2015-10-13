# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class Dereferer(SimpleCrypter):
    __name__    = "Dereferer"
    __type__    = "crypter"
    __version__ = "0.19"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/.*?(?P<LINK>(?:ht|f)tps?://.+)'
    __config__  = [("activated", "bool", "Activated", True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Crypter for dereferers"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN = None
    PLUGIN_NAME   = None


    def _log(self, level, plugintype, pluginname, messages):
        return super(Dereferer, self)._log(level, plugintype, pluginname, (self.PLUGIN_NAME,) + messages)


    def init(self):
        super(Dereferer, self).init()

        self.__pattern__ = self.pyload.pluginManager.crypterPlugins[self.classname]['pattern']  #@TODO: Recheck in 0.4.10

        self.PLUGIN_DOMAIN = re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        self.PLUGIN_NAME   = "".join(part.capitalize() for part in re.split(r'(\.|\d+)', self.PLUGIN_DOMAIN) if part != '.')


    def get_links(self):
        return [re.match(self.__pattern__, self.pyfile.url).group('LINK')]
