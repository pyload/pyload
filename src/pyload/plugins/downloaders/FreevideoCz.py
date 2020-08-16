# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class FreevideoCz(DeadDownloader):
    __name__ = "FreevideoCz"
    __type__ = "downloader"
    __version__ = "0.35"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?freevideo\.cz/vase-videa/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Freevideo.cz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
