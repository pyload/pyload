# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class WarserverCz(DeadDownloader):
    __name__ = "WarserverCz"
    __type__ = "downloader"
    __version__ = "0.18"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?warserver\.cz/stahnout/\d+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Warserver.cz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]
