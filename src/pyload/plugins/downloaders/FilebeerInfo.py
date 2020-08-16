# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class FilebeerInfo(DeadDownloader):
    __name__ = "FilebeerInfo"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?filebeer\.info/(?!\d*~f)(?P<ID>\w+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Filebeer.info plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
