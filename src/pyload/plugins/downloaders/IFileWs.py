# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class IFileWs(DeadDownloader):
    __name__ = "IFileWs"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?ifile\.ws/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Ifile.ws downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("z00nx", "z00nx0@gmail.com")]
