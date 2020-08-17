# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class CloudzerNet(DeadDownloader):
    __name__ = "CloudzerNet"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?(cloudzer\.net/file/|clz\.to/(file/)?)\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Cloudzer.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("gs", "I-_-I-_-I@web.de"),
        ("z00nx", "z00nx0@gmail.com"),
        ("stickell", "l.stickell@yahoo.it"),
    ]
