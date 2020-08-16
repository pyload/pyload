# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class SpeedfileCz(DeadDownloader):
    __name__ = "SpeedFileCz"
    __type__ = "downloader"
    __version__ = "0.37"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?speedfile\.cz/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Speedfile.cz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
