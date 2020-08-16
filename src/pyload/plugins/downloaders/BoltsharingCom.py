# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class BoltsharingCom(DeadDownloader):
    __name__ = "BoltsharingCom"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?boltsharing\.com/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Boltsharing.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
