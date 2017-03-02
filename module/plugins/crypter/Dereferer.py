# -*- coding: utf-8 -*-

import re

from ..internal.SimpleCrypter import SimpleCrypter


class Dereferer(SimpleCrypter):
    __name__ = "Dereferer"
    __type__ = "crypter"
    __version__ = "0.26"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-]{3,63}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/.*?(?P<LINK>[\w^_]+://.+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Universal link dereferer"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = None
    PLUGIN_NAME = None

    DIRECT_LINK = False

    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.PLUGIN_NAME,) + messages
        return SimpleCrypter._log(
            self, level, plugintype, pluginname, messages)

    def init(self):
        self.__pattern__ = self.pyload.pluginManager.crypterPlugins[
            self.classname]['pattern']  # @TODO: Recheck in 0.4.10

        self.PLUGIN_DOMAIN = re.match(
            self.__pattern__,
            self.pyfile.url).group("DOMAIN").lower()
        self.PLUGIN_NAME = "".join(
            part.capitalize() for part in re.split(
                r'\.|\d+|-', self.PLUGIN_DOMAIN) if part != '.')

    def get_links(self):
        return [self.info['pattern']['LINK']]
