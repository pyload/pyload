# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class ShareFilesCo(DeadDownloader):
    __name__ = "ShareFilesCo"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?sharefiles\.co/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Sharefiles.co downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
