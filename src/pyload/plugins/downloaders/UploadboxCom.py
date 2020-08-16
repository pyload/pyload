# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class UploadboxCom(DeadDownloader):
    __name__ = "Uploadbox"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?uploadbox\.com/files/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """UploadBox.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
