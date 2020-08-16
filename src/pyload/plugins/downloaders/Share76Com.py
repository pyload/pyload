# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class Share76Com(DeadDownloader):
    __name__ = "Share76Com"
    __type__ = "downloader"
    __version__ = "0.09"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?share76\.com/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Share76.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = []
