# -*- coding: utf-8 -*-
#
# Test links:
# http://data.hu/get/6381232/random.bin

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class DataHu(SimpleHoster):
    __name__    = "DataHu"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?data\.hu/get/\w+'

    __description__ = """Data.hu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("crash", ""),
                       ("stickell", "l.stickell@yahoo.it")]


    INFO_PATTERN = ur'<title>(?P<N>.*) \((?P<S>[^)]+)\) let\xf6lt\xe9se</title>'
    OFFLINE_PATTERN = ur'Az adott f\xe1jl nem l\xe9tezik'
    LINK_PATTERN = r'<div class="download_box_button"><a href="([^"]+)">'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = self.premium


    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_PATTERN not found"))

        self.download(m.group(1), disposition=True)


getInfo = create_getInfo(DataHu)
