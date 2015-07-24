# -*- coding: utf-8 -*
#
# Test links:
#   http://forum.xda-developers.com/devdb/project/dl/?id=10885

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class XdadevelopersCom(SimpleHoster):
    __name__    = "XdadevelopersCom"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?forum\.xda-developers\.com/devdb/project/dl/\?id=\d+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Xda-developers.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'<label>Filename:</label>\s*<div>\s*(?P<N>.*?)\n'
    SIZE_PATTERN    = r'<label>Size:</label>\s*<div>\s*(?P<S>[\d.,]+)(?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'</i> Device Filter</h3>'


    def setup(self):
        self.multiDL        = True
        self.resume_download = True
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        self.link = pyfile.url + "&task=get"  #@TODO: Revert to `get={'task': "get"}` in 0.4.10


getInfo = create_getInfo(XdadevelopersCom)
