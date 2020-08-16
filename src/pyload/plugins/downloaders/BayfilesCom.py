# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class BayfilesCom(DeadDownloader):
    __name__ = "BayfilesCom"
    __type__ = "downloader"
    __version__ = "0.14"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?bayfiles\.(com|net)/file/(?P<ID>\w+/\w+/[^/]+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Bayfiles.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]
