# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class EgoFilesCom(DeadDownloader):
    __name__ = "EgoFilesCom"
    __type__ = "downloader"
    __version__ = "0.21"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?egofiles\.com/\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Egofiles.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
