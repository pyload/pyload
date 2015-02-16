# -*- coding: utf-8 -*-
#
# Test links:
#   http://d-h.st/mM8

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class DevhostSt(SimpleHoster):
    __name    = "DevhostSt"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?d-h\.st/(?!users/)\w{3}'

    __description = """d-h.st hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN      = r'<span title="(?P<N>.*?)"'
    SIZE_PATTERN      = r'</span> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)<br'
    HASHSUM_PATTERN   = r'>(?P<T>.*?) Sum</span>: &nbsp;(?P<H>.*?)<br'

    OFFLINE_PATTERN   = r'>File Not Found'
    LINK_FREE_PATTERN = r'var product_download_url= \'(.+?)\''


    def setup(self):
        self.multiDL    = True
        self.chunkLimit = 1
