# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class NowVideoAt(SimpleHoster):
    __name__    = "NowVideoAt"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?nowvideo\.(at|ch|co|eu|sx)/(video|mobile/#/videos)/(?P<ID>\w+)'

    __description__ = """NowVideo.at hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern__, r'http://www.nowvideo.at/video/\g<ID>')]

    NAME_PATTERN = r'<h4>(?P<N>.+?)<'
    OFFLINE_PATTERN = r'>This file no longer exists'

    LINK_FREE_PATTERN = r'<source src="(.+?)"'
    LINK_PREMIUM_PATTERN = r'<div id="content_player" >\s*<a href="(.+?)"'


    def setup(self):
        self.multiDL = True
        self.resumeDownload = True


    def handleFree(self):
        self.html = self.load("http://www.nowvideo.at/mobile/video.php", get={'id': self.info['ID']})

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))

        self.download(m.group(1))


getInfo = create_getInfo(NowVideoAt)
