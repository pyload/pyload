# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class BitshareCom(DeadDownloader):
    __name__ = "BitshareCom"
    __type__ = "downloader"
    __version__ = "0.62"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?bitshare\.com/(files/)?(?(1)|\?f=)(?P<ID>\w+)(?(1)/(?P<NAME>.+?)\.html)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Bitshare.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Paul King", None), ("fragonib", "fragonib[AT]yahoo[DOT]es")]
