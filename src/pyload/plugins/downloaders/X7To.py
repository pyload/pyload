# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class X7To(DeadDownloader):
    __name__ = "X7To"
    __type__ = "downloader"
    __version__ = "0.46"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?x7\.to/"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """X7.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("ernieb", "ernieb")]
