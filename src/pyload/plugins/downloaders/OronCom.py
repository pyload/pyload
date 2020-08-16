# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class OronCom(DeadDownloader):
    __name__ = "OronCom"
    __type__ = "downloader"
    __version__ = "0.19"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?oron\.com/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Oron.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("chrox", "chrox@pyload.net"), ("DHMH", "DHMH@pyload.net")]
