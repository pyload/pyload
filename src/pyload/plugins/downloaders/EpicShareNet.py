# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class EpicShareNet(DeadDownloader):
    __name__ = "EpicShareNet"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?epicshare\.net/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """EpicShare.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]
