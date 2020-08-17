# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class UploadkingCom(DeadDownloader):
    __name__ = "UploadkingCom"
    __type__ = "downloader"
    __version__ = "0.19"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?uploadking\.com/\w{10}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """UploadKing.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
