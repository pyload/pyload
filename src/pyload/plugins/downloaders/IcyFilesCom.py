# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class IcyFilesCom(DeadDownloader):
    __name__ = "IcyFilesCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?icyfiles\.com/(.+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """IcyFiles.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]
