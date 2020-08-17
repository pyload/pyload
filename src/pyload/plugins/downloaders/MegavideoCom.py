# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class MegavideoCom(DeadDownloader):
    __name__ = "MegavideoCom"
    __type__ = "downloader"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?megavideo\.com/\?.*&?(d|v)=\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Megavideo.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"), ("mkaay", "mkaay@mkaay.de")]
