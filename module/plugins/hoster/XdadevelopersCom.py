# -*- coding: utf-8 -*-
# http://forum.xda-developers.com/devdb/project/dl/?id=10885

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class XdadevelopersCom(SimpleHoster):
    __name__    = "XdadevelopersCom"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?forum.xda-developers.com/devdb/project/dl/\?id=\d+'

    __description__ = """forum.xdadevelopers.com hoster plugin (DevDB)"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN = r'<label>Filename:</label>\n\t\t\t\t\t<div>\n\t\t\t\t\t(?P<N>.*?)\n\t\t\t\t\t</div>'
    SIZE_PATTERN = r'<label>Size:</label>\n\t\t\t\t\t<div>\n\t\t\t\t\t(?P<S>[\d.]+)(?P<U>[kKmMgGbB]+)\n\t\t\t\t\t</div>\n'

    OFFLINE_PATTERN = r'</i> Device Filter</h3>'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1

    def handleFree(self, pyfile):        
        self.download(pyfile.url+"&task=get",cookies=True,disposition=True)

getInfo = create_getInfo(XdadevelopersCom)
