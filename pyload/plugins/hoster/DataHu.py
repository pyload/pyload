# -*- coding: utf-8 -*-
#
# Test links:
# http://data.hu/get/6381232/random.bin

import re

from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DataHu(SimpleHoster):
    __name__ = "DataHu"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?data.hu/get/\w+'

    __description__ = """Data.hu hoster plugin"""
    __author_name__ = ("crash", "stickell")
    __author_mail__ = "l.stickell@yahoo.it"

    FILE_INFO_PATTERN = ur'<title>(?P<N>.*) \((?P<S>[^)]+)\) let\xf6lt\xe9se</title>'
    OFFLINE_PATTERN = ur'Az adott f\xe1jl nem l\xe9tezik'
    LINK_PATTERN = r'<div class="download_box_button"><a href="([^"]+)">'


    def handleFree(self):
        self.resumeDownload = True
        self.html = self.load(self.pyfile.url, decode=True)

        m = re.search(self.LINK_PATTERN, self.html)
        if m:
            url = m.group(1)
            self.logDebug('Direct link: ' + url)
        else:
            self.parseError('Unable to get direct link')

        self.download(url, disposition=True)


getInfo = create_getInfo(DataHu)
