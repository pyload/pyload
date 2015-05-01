# -*- coding: utf-8 -*-
#
# Test links:
#   http://data.hu/get/6381232/random.bin

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class DataHu(SimpleHoster):
    __name    = "DataHu"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?data\.hu/get/\w+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Data.hu hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("crash", ""),
                       ("stickell", "l.stickell@yahoo.it")]


    INFO_PATTERN = ur'<title>(?P<N>.*) \((?P<S>[^)]+)\) let\xf6lt\xe9se</title>'
    OFFLINE_PATTERN = ur'Az adott f\xe1jl nem l\xe9tezik'
    LINK_FREE_PATTERN = r'<div class="download_box_button"><a href="(.+?)">'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = self.premium
