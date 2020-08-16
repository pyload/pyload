# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class NowVideoSx(SimpleDownloader):
    __name__ = "NowVideoSx"
    __type__ = "downloader"
    __version__ = "0.17"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?nowvideo\.[a-zA-Z]{2,}/(video/|mobile/(#/videos/|.+?id=))(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """NowVideo.sx downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"http://www.nowvideo.sx/video/\g<ID>")]

    NAME_PATTERN = r"<h4>(?P<N>.+?)<"
    OFFLINE_PATTERN = r">This file no longer exists"

    LINK_FREE_PATTERN = r'<source src="(.+?)"'
    LINK_PREMIUM_PATTERN = r'<div id="content_player" >\s*<a href="(.+?)"'

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def handle_free(self, pyfile):
        self.data = self.load(
            "http://www.nowvideo.sx/mobile/video.php",
            get={"id": self.info["pattern"]["ID"]},
        )

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
