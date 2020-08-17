# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class SpeedLoadOrg(DeadDownloader):
    __name__ = "SpeedLoadOrg"
    __type__ = "downloader"
    __version__ = "1.07"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?speedload\.org/(?P<ID>\w+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Speedload.org downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
