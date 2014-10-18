# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSPAccount import XFSPAccount


class XFileSharingPro(XFSPAccount):
    __name__ = "XFileSharingPro"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """XFileSharingPro multi-purpose account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    def init(self):
        pattern = self.core.pluginManager.hosterPlugins[self.__name__]['pattern']
        self.HOSTER_NAME = re.match(pattern, self.pyfile.url).group(1).lower()
