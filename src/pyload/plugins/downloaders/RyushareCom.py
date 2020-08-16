# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class RyushareCom(DeadDownloader):
    __name__ = "RyushareCom"
    __type__ = "downloader"
    __version__ = "0.32"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?ryushare\.com/\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Ryushare.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("quareevo", "quareevo@arcor.de"),
    ]
