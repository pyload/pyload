# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class IfileIt(DeadDownloader):
    __name__ = "IfileIt"
    __type__ = "downloader"
    __version__ = "0.34"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Ifile.it downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
