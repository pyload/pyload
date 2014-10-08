# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class XFileSharingPro(XFSPHoster):
    __name__ = "XFileSharingPro"
    __type__ = "hoster"
    __version__ = "0.38"

    __pattern__ = r'^unmatchable$'

    __description__ = """XFileSharingPro dummy hoster plugin for hook"""
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    FILE_URL_REPLACEMENTS = [(r'/embed-(\w{12}).*', r'/\1')]  #: support embedded files


    def setup(self):
        self.chunkLimit = 1
        self.multiDL = True

        self.__pattern__ = self.core.pluginManager.hosterPlugins[self.__name__]['pattern']
        self.HOSTER_NAME = re.match(self.__pattern__, self.pyfile.url).group(1).lower()


getInfo = create_getInfo(XFileSharingPro)
