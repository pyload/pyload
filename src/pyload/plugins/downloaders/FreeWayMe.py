# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class FreeWayMe(DeadDownloader):
    __name__ = "FreeWayMe"
    __type__ = "downloader"
    __version__ = "0.25"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?free-way\.(bz|me)/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """FreeWayMe multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Nicolas Giese", "james@free-way.me")]
