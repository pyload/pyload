# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class ZShareNet(DeadDownloader):
    __name__ = "ZShareNet"
    __type__ = "downloader"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r"https?://(?:ww[2w]\.)?zshares?\.net/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """ZShare.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("espes", None), ("Cptn Sandwich", None)]
