# -*- coding: utf-8 -*-
#
# Test links:
#   http://d-h.st/mM8

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DevhostSt(SimpleHoster):
    __name__    = "DevhostSt"
    __type__    = "hoster"
    __version__ = "0.06"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?d-h\.st/(?!users/)\w{3}'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """D-h.st hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN      = r'<span title="(?P<N>.*?)"'
    SIZE_PATTERN      = r'</span> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)<br'
    HASHSUM_PATTERN   = r'>(?P<T>.*?) Sum</span>: &nbsp;(?P<H>.*?)<br'

    OFFLINE_PATTERN   = r'>File Not Found'
    LINK_FREE_PATTERN = r'var product_download_url= \'(.+?)\''


    def setup(self):
        self.multiDL    = True
        self.chunk_limit = 1


getInfo = create_getInfo(DevhostSt)
