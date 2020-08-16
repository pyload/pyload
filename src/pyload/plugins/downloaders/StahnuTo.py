# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class StahnuTo(DeadDownloader):
    __name__ = "StahnuTo"
    __type__ = "downloader"
    __version__ = "0.16"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?stahnu\.to/(files/get/|.*\?file=)([^/]+).*"
    __config__ = []

    __description__ = """Stahnu.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", None)]
