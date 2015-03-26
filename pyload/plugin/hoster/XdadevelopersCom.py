# -*- coding: utf-8 -*
#
# Test links:
#   http://forum.xda-developers.com/devdb/project/dl/?id=10885

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class XdadevelopersCom(SimpleHoster):
    __name    = "XdadevelopersCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'https?://(?:www\.)?forum\.xda-developers\.com/devdb/project/dl/\?id=\d+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Xda-developers.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'<label>Filename:</label>\s*<div>\s*(?P<N>.*?)\n'
    SIZE_PATTERN    = r'<label>Size:</label>\s*<div>\s*(?P<S>[\d.,]+)(?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'</i> Device Filter</h3>'


    def setup(self):
        self.multiDL        = True
        self.resumeDownload = True
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        self.link = pyfile.url + "&task=get"  #@TODO: Revert to `get={'task': "get"}` in 0.4.10
