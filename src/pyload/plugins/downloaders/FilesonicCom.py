# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class FilesonicCom(DeadDownloader):
    __name__ = "FilesonicCom"
    __type__ = "downloader"
    __version__ = "0.41"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?filesonic\.com/file/\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Filesonic.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"), ("paulking", None)]
