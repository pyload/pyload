# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class DodanePl(DeadDownloader):
    __name__ = "DodanePl"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?dodane\.pl/file/\d+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Dodane.pl downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("z00nx", "z00nx0@gmail.com")]
