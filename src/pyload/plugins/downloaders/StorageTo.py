# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class StorageTo(DeadDownloader):
    __name__ = "StorageTo"
    __type__ = "downloader"
    __version__ = "0.06"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?storage\.to/get/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Storage.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de")]
