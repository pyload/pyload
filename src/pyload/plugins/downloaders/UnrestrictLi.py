# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class UnrestrictLi(DeadDownloader):
    __name__ = "UnrestrictLi"
    __type__ = "downloader"
    __version__ = "0.28"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?(unrestrict|unr)\.li/dl/[\w^_]+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Unrestrict.li multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
