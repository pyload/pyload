# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class SharingmatrixCom(DeadDownloader):
    __name__ = "SharingmatrixCom"
    __type__ = "downloader"
    __version__ = "0.06"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?sharingmatrix\.com/file/\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Sharingmatrix.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"), ("paulking", None)]
