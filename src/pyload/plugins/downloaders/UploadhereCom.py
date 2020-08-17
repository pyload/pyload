# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class UploadhereCom(DeadDownloader):
    __name__ = "UploadhereCom"
    __type__ = "downloader"
    __version__ = "0.17"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?uploadhere\.com/\w{10}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Uploadhere.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
