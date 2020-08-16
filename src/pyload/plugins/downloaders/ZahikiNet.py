# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class ZahikiNet(DeadDownloader):
    __name__ = "ZahikiNet"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?zahiki\.net/\w+/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Zahiki.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]
