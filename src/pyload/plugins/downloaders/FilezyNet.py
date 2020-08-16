# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class FilezyNet(DeadDownloader):
    __name__ = "FilezyNet"
    __type__ = "downloader"
    __version__ = "0.25"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?filezy\.net/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Filezy.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = []
