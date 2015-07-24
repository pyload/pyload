# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class NowVideoSx(SimpleHoster):
    __name__    = "NowVideoSx"
    __type__    = "hoster"
    __version__ = "0.13"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?nowvideo\.[a-zA-Z]{2,}/(video/|mobile/(#/videos/|.+?id=))(?P<ID>\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """NowVideo.sx hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://www.nowvideo.sx/video/\g<ID>')]

    NAME_PATTERN = r'<h4>(?P<N>.+?)<'
    OFFLINE_PATTERN = r'>This file no longer exists'

    LINK_FREE_PATTERN = r'<source src="(.+?)"'
    LINK_PREMIUM_PATTERN = r'<div id="content_player" >\s*<a href="(.+?)"'


    def setup(self):
        self.resume_download = True
        self.multiDL        = True


    def handle_free(self, pyfile):
        self.html = self.load("http://www.nowvideo.sx/mobile/video.php", get={'id': self.info['pattern']['ID']})

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))

        self.link = m.group(1)


getInfo = create_getInfo(NowVideoSx)
