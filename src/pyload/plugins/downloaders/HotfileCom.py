# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class HotfileCom(DeadDownloader):
    __name__ = "HotfileCom"
    __type__ = "downloader"
    __version__ = "0.42"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?hotfile\.com/dl/\d+/\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Hotfile.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("sitacuisses", "sitacuisses@yhoo.de"),
        ("spoob", "spoob@pyload.net"),
        ("mkaay", "mkaay@mkaay.de"),
        ("JoKoT3", "jokot3@gmail.com"),
    ]
