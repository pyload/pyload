# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class HellspyCz(DeadDownloader):
    __name__ = "HellspyCz"
    __type__ = "downloader"
    __version__ = "0.33"
    __status__ = "stable"

    __pattern__ = (
        r"http://(?:www\.)?(?:hellspy\.(?:cz|com|sk|hu|pl)|sciagaj\.pl)(/\S+/\d+)"
    )
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """HellSpy.cz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
