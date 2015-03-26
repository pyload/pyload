# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class NowVideoSx(SimpleHoster):
    __name    = "NowVideoSx"
    __type    = "hoster"
    __version = "0.12"

    __pattern = r'http://(?:www\.)?nowvideo\.[a-zA-Z]{2,}/(video/|mobile/(#/videos/|.+?id=))(?P<ID>\w+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """NowVideo.sx hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern + ".*", r'http://www.nowvideo.sx/video/\g<ID>')]

    NAME_PATTERN = r'<h4>(?P<N>.+?)<'
    OFFLINE_PATTERN = r'>This file no longer exists'

    LINK_FREE_PATTERN = r'<source src="(.+?)"'
    LINK_PREMIUM_PATTERN = r'<div id="content_player" >\s*<a href="(.+?)"'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self, pyfile):
        self.html = self.load("http://www.nowvideo.sx/mobile/video.php", get={'id': self.info['pattern']['ID']})

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))

        self.download(m.group(1))
