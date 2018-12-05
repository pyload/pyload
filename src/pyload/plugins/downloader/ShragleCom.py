# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class ShragleCom(DeadDownloader):
    __name__ = "ShragleCom"
    __type__ = "downloader"
    __version__ = "0.27"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?(cloudnator|shragle)\.com/files/(?P<ID>.+?)/"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Cloudnator.com (Shragle.com) downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net"), ("zoidberg", "zoidberg@mujmail.cz")]
