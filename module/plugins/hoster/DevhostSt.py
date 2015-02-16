# -*- coding: utf-8 -*-
#
# Test links:
#   http://d-h.st/mM8

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class DevhostSt(SimpleHoster):
    __name__    = "DevhostSt"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?d-h\.st/(?!users/)\w{3}'

    __description__ = """d-h.st hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN      = r'<span title="(?P<N>.*?)"'
    SIZE_PATTERN      = r'</span> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)<br'
    HASHSUM_PATTERN   = r'>(?P<T>.*?) Sum</span>: &nbsp;(?P<H>.*?)<br'

    OFFLINE_PATTERN   = r'>File Not Found'
    LINK_FREE_PATTERN = r'var product_download_url= \'(.+?)\''


    def setup(self):
        self.multiDL    = True
        self.chunkLimit = 1


getInfo = create_getInfo(DevhostSt)
