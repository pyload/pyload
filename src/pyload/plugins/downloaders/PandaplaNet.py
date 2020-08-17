# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class PandaplaNet(DeadDownloader):
    __name__ = "PandaplaNet"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?pandapla\.net/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Pandapla.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]
