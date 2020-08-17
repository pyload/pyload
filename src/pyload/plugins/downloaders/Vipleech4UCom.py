# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class Vipleech4UCom(DeadDownloader):
    __name__ = "Vipleech4UCom"
    __type__ = "downloader"
    __version__ = "0.25"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?vipleech4u\.com/manager\.php"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Vipleech4u.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Kagenoshin", "kagenoshin@gmx.ch")]
