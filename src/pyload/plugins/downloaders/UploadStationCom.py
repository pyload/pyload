# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class UploadStationCom(DeadDownloader):
    __name__ = "UploadStationCom"
    __type__ = "downloader"
    __version__ = "0.57"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?uploadstation\.com/file/(?P<ID>\w+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """UploadStation.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("fragonib", "fragonib[AT]yahoo[DOT]es"),
        ("zoidberg", "zoidberg@mujmail.cz"),
    ]
